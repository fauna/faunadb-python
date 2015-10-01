from functools import partial

from ..errors import InvalidQuery, InvalidValue
from ..objects import Page, Ref
from .. import query
from .field import Field
from ._util import dict_dup, get_path, set_path, calculate_diff


class _ModelMetaClass(type):
  """
  The methods in ModelMetaClass can be called on :any:`Method` classes.
  (On the class. **Not** on its instances.)
  """

  def __init__(cls, name, bases, dct):
    # Need to call it `self` or sphynx won't document properties.
    # pylint: disable=bad-mcs-method-argument

    class_name = dct.get("__fauna_class_name__")
    if class_name is not None:
      cls.__fauna_class_name__ = class_name
      cls.class_ref = Ref("classes", class_name)
      cls.fields = {}

      for key, value in dct.items():
        if cls._maybe_add_field(key, value):
          del dct[key]

    super(_ModelMetaClass, cls).__init__(name, bases, dct)

  def __setattr__(cls, key, value):
    if not cls._maybe_add_field(key, value):
      super(_ModelMetaClass, cls).__setattr__(key, value)


class Model(object):
  """
  Base class for all models.

  Models represent database instances.
  They link a FaunaDB class to a Python class.
  See the `docs <https://faunadb.com/documentation#objects>`__.

  The basic format is::

    class MyModel(Model):
      __fauna_class_name__ = 'my_models'
      my_field = Field()
    # Fields can be added even after the class has been defined.
    MyModel.other_field = Field()

  Properties will be generated for each :any:`Field`.

  :samp:`__fauna_class_name__` is mandatory; otherwise this will be treated as an abstract class.

  :any:`Class` :py:meth:`create_for_model` must be called before you can use the model.
  """

  __metaclass__ = _ModelMetaClass

  # These fields are filled in by _ModelMetaClass, but write them here so
  # we can document them and PyLint doesn't give us no-member errors.

  #: Name of the class in the database.
  #: If this is not set, this will be considered to be an abstract class.
  __fauna_class_name__ = None

  #: :any:`Ref` for the class itself.
  #:
  #: :samp:`instance.ref` should be the same as
  #: :samp:`Ref(instance.__class__.class_ref, instance.id())`.
  class_ref = None

  #: Dict {field_name: :any:`Field`} of all fields assigned to this class.
  fields = None

  def __init__(self, client, **data):
    self.client = client
    """Client instance that the model uses to save to the database."""

    # JSON data of the instance before any changes were made. (Empty for new instance).
    self._original = {}
    self._init_state()

    for field_name in data:
      if field_name not in self.__class__.fields:
        raise InvalidValue("No such field %s" % field_name)
      setattr(self, field_name, data[field_name])

  #region Common properties
  @property
  def ref(self):
    """:any:`Ref` of this instance in the database. :samp:`None` iff :py:meth:`is_new_instance`."""
    return self._current.get("ref")

  @property
  def ts(self):
    """
    Microsecond UNIX Timestamp of latest :py:meth:`save`.
    :samp:`None` iff :py:meth:`is_new_instance`.
    """
    return self._current.get("ts")

  @property
  def id(self):
    """The id portion of this instance's :any:`Ref`."""
    if self.is_new_instance():
      raise InvalidQuery("Instance has not been saved to the database, so no id exists.")
    return self.ref.id()
  #endregion

  def get_encoded(self, field_name):
    """Gets the encoded value for a field."""
    field = self.__class__.fields[field_name]
    return get_path(field.path, self._current)

  #region Persistence
  def is_new_instance(self):
    """
    :samp:`False` if this has ever been saved to the database.
    Iff :samp:`True`, :any:`ref` and :any:`ts` will be :samp:`None`.
    """
    return self.ref is None

  def delete(self):
    """Removes this instance from the database."""
    self.client.query(self.delete_query())

  def delete_query(self):
    """Query that deletes this instance."""
    if self.is_new_instance():
      raise InvalidQuery("Instance does not exist in the database.")
    return query.delete(self.ref)

  def save(self, replace=False):
    """Executes :py:meth:`save_query`."""
    self._init_from_resource(self.client.query(self.save_query(replace)))

  def save_query(self, replace=False):
    """
    Query to save this instance to the database.
    If :py:meth:`is_new_instance`, creates it and sets :any:`ref` and :any:`ts`.
    Otherwise, updates any changed fields.

    :param replace:
      If true, updates will update *all* fields
      using :py:meth:`replace_query` instead of :py:meth:`update_query`.
      See the `docs <https://faunadb.com/documentation#queries-write_functions>`_.
    """
    if self.is_new_instance():
      return self.create_query()
    elif replace:
      return self.replace_query()
    else:
      return self.update_query()

  def create_query(self):
    """
    Query to create a new instance.
    It is recommended to use :py:meth:`save_query` instead.
    """
    if not self.is_new_instance():
      raise InvalidQuery("Trying to create instance that has already been created.")
    cls = self.__class__
    return query.create(cls.class_ref, query.quote(self._current))

  def replace_query(self):
    """
    Query to replace this instance's data.
    It is recommended to use :samp:`instance.save_query(replace=True)` instead.
    """
    if self.is_new_instance():
      raise InvalidQuery("Instance has not yet been created.")
    return query.replace(self.ref, query.quote(self._current))

  def update_query(self):
    """
    Query to update this instance's data.
    It is recommended to use :py:meth:`save_query` instead.
    """
    if self.is_new_instance():
      raise InvalidQuery("Instance has not yet been created.")
    return query.update(self.ref, query.quote(self._diff()))
  #endregion

  #region Standard methods
  def __eq__(self, other):
    # pylint: disable=protected-access
    return self is other or self._current == other._current

  def __ne__(self, other):
    return not self == other

  def __repr__(self):
    fields = [field + "=" + str(getattr(self, field)) for field in self.__class__.fields]
    return "%s(ref=%s, ts=%s, %s)" % (self.__class__.__name__, self.ref, self.ts, ', '.join(fields))
  #endregion

  #region Class methods
  @classmethod
  def is_abstract(cls):
    """A Model class is considered abstract if __fauna_class_name__ is not set."""
    return cls.__fauna_class_name__ is None

  @classmethod
  def get(cls, client, ref):
    """Gets the instance of this class specified by :samp:`ref`."""
    return cls.get_from_resource(client, client.get(ref))

  @classmethod
  def get_by_id(cls, client, instance_id):
    """Gets the instance of this class specified by :samp:`id`."""
    return cls.get(client, Ref(cls.class_ref, instance_id))

  @classmethod
  def create(cls, client, *args, **kwargs):
    # pylint: disable=protected-access
    instance = cls(client, *args, **kwargs)
    instance._init_from_resource(client.query(instance.create_query()))
    return instance

  @classmethod
  def get_from_resource(cls, client, resource):
    """Creates a new instance from query results."""
    # pylint: disable=protected-access
    instance = cls(client)
    instance._init_from_resource(resource)
    return instance

  @classmethod
  def page(cls, client, instance_set, page_size=None, before=None, after=None):
    """
    Paginates a set query and converts results to instances of this class.

    :param instance_set:
      :any:`Set` of instances of this class.
    :param size:
      Number of instances per page.
    :param before:
      :any:`Ref` of the previous instance. Exclusive with :samp:`after`.
    :param after:
      :any:`Ref` of the next instance. Exclusive with :samp:`before`.
    :return:
      Page whose data is a list of instances of this class.
    """
    get = query.lambda_expr("x", query.get(query.var("x")))
    return cls._map_page(client, instance_set, get, page_size=page_size, before=before, after=after)

  @classmethod
  def iterator(cls, client, instance_set, page_size=None):
    """
    Returns an iterator of model instances.
    :param instance_set: :any:`Set` of refs to instances of this class.
    """
    m = query.lambda_expr("x", query.get(query.var("x")))
    iterator = Page.set_iterator(client, instance_set, page_size=page_size, map_lambda=m)
    for instance in iterator:
      yield cls.get_from_resource(client, instance)

  @classmethod
  def page_index(cls, index, matched_values, page_size=None, before=None, after=None):
    """
    Calls :any:`Index` :py:meth:`match` and then works just like :py:meth:`page`.

    :param matched_values:
      Value
    """
    if not isinstance(matched_values, list):
      matched_values = [matched_values]
    client = index.client
    match_set = index.match(*matched_values)
    getter = Model._index_ref_getter(index)
    return cls._map_page(client, match_set, getter, page_size=page_size, before=before, after=after)

  @classmethod
  def iter_index(cls, index, matched_values, page_size=None):
    client = index.client
    if not isinstance(matched_values, list):
      matched_values = [matched_values]
    match_set = index.match(*matched_values)

    getter = Model._index_ref_getter(index)
    iterator = Page.set_iterator(client, match_set, page_size=page_size, map_lambda=getter)
    for instance in iterator:
      yield cls.get_from_resource(client, instance)
  #endregion

  #region Private methods
  def _init_from_resource(self, resource):
    if resource["class"] != self.__class__.class_ref:
      raise InvalidValue("Trying to initialize from resource of class %s; expected %s." %
                         (resource["class"], self.__class__.class_ref))
    self._original = resource
    self._init_state()

  def _init_state(self):
    # New JSON data of the instance.
    self._current = dict_dup(self._original)
    # Dict from field names to decoded values. Only used for fields with a codec.
    self._cache = {}

  def _diff(self):
    return calculate_diff(self._original, self._current)
  #endregion

  #region Private class methods
  @staticmethod
  def _index_ref_getter(index):
    """
    Lambda expression for getting an instance Ref out of a match result.
    """
    if index.values:
      return query.lambda_expr("arr", query.get(query.select(len(index.values), query.var("arr"))))
    else:
      return query.lambda_expr("x", query.get(query.var("x")))

  @classmethod
  def _map_page(cls, client, instance_set, page_lambda, page_size=None, before=None, after=None):
    """
    Creates a query to call `page_lambda` on page data, which should fetch instance data.
    Then maps the result page to create Model instances out of that instance data.
    """
    page_query = query.paginate(instance_set, size=page_size, before=before, after=after)
    map_query = query.map(page_lambda, page_query)
    page = Page.from_raw(client.query(map_query))
    return page.map_data(partial(cls.get_from_resource, client))

  @classmethod
  def _maybe_add_field(cls, field_name, field):
    """Add the property to cls.fields if it is a Field."""
    is_field = isinstance(field, Field)
    if is_field:
      if field.path is None:
        field.path = ["data", field_name]
      cls._add_field(field_name, field)
    return is_field

  @classmethod
  def _add_field(cls, field_name, field):
    """Add the field to cls.fields and generate a getter and setter."""
    # pylint: disable=missing-docstring, protected-access

    if field_name in ("ref", "ts"):
      raise RuntimeError("Forbidden field name.")

    cls.fields[field_name] = field

    if field.codec is None:
      def getter(self):
        return get_path(field.path, self._current)
      def setter(self, value):
        set_path(field.path, value, self._current)
    else:
      def getter(self):
        if field_name in self._cache:
          return self._cache[field_name]
        else:
          encoded = get_path(field.path, self._current)
          decoded = field.codec.decode(encoded, self)
          self._cache[field_name] = decoded
          return decoded

      def setter(self, value):
        self._cache[field_name] = value
        encoded = field.codec.encode(value, self)
        set_path(field.path, encoded, self._current)

    setattr(cls, field_name, property(getter, setter))
  #endregion
