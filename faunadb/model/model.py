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

  :any:`Class.create_for_model` must be called before you can save model instances.
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
  #: :samp:`Ref(instance.__class__.class_ref, instance.id)`.
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
    """:any:`Ref` of this instance in the database. Fails if :any:`is_new_instance`."""
    if self.is_new_instance():
      raise InvalidQuery("Instance has not been saved to the database, so no ref exists.")
    return self._current["ref"]

  @property
  def id(self):
    """The id portion of this instance's :any:`Ref`. Fails if any:`is_new_instance`."""
    return self.ref.id()

  @property
  def ts(self):
    """Microsecond UNIX timestamp of latest :any:`save`. Fails if :any:`is_new_instance`."""
    if self.is_new_instance():
      raise InvalidQuery("Instance has not been saved to the database, so no ts exists.")
    return self._current["ts"]
  #endregion

  def get_encoded(self, field_name):
    """For a field with a :any:`Codec`, gets the encoded value."""
    field = self.__class__.fields[field_name]
    return get_path(field.path, self._current)

  #region Persistence
  def is_new_instance(self):
    """
    :samp:`False` if this has ever been saved to the database.
    Iff :samp:`True`, :any:`ref` and :any:`ts` will fail.
    """
    return "ref" not in self._current

  def delete(self):
    """Removes this instance from the database."""
    self.client.query(self.delete_query())

  def delete_query(self):
    """Query that deletes this instance."""
    if self.is_new_instance():
      raise InvalidQuery("Instance does not exist in the database.")
    return query.delete(self.ref)

  def save(self, replace=False):
    """Executes :any:`save_query`."""
    self._init_from_resource(self.client.query(self.save_query(replace)))

  def save_query(self, replace=False):
    """
    Query to save this instance to the database.
    If :any:`is_new_instance`, creates it and sets :any:`ref` and :any:`ts`.
    Otherwise, updates any changed fields.

    :param replace:
      If true, updates will update *all* fields
      using :any:`replace_query` instead of :any:`update_query`.
      See the `docs <https://faunadb.com/documentation/queries#write_functions>`_.
    """
    if self.is_new_instance():
      return self.create_query()
    elif replace:
      return self.replace_query()
    else:
      return self.update_query()

  def create_query(self):
    """Query to create a new instance."""
    if not self.is_new_instance():
      raise InvalidQuery("Trying to create instance that has already been created.")
    return query.create(self.__class__.class_ref, query.quote(self._current))

  def replace_query(self):
    """Query to replace this instance's data."""
    if self.is_new_instance():
      raise InvalidQuery("Instance has not yet been created.")
    return query.replace(self.ref, query.quote(self._current))

  def update_query(self):
    """Query to update this instance's data."""
    if self.is_new_instance():
      raise InvalidQuery("Instance has not yet been created.")
    return query.update(self.ref, query.quote(self._diff()))
  #endregion

  #region Standard methods
  def __eq__(self, other):
    # pylint: disable=protected-access
    return self is other or (isinstance(other, Model) and self._current == other._current)

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
  def create(cls, client, **data):
    """Initializes and saves a new instance."""
    # pylint: disable=protected-access
    instance = cls(client, **data)
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
      Query set of instances of this class.
    :param size:
      Number of instances per page.
    :param before:
      :any:`Ref` of the previous instance. Exclusive with :samp:`after`.
    :param after:
      :any:`Ref` of the next instance. Exclusive with :samp:`before`.
    :return:
      Page whose data is a list of instances of this class.
    """
    return cls._map_page(
      client, instance_set, query.get,
      page_size=page_size, before=before, after=after)

  @classmethod
  def iterator(cls, client, instance_set, page_size=None):
    """
    Returns an iterator of model instances.
    :param instance_set: :any:`Set` of refs to instances of this class.
    """
    def mapper(instance):
      return cls.get_from_resource(client, instance)
    return Page.set_iterator(
      client, instance_set,
      page_size=page_size, map_lambda=query.get, mapper=mapper)

  @classmethod
  def page_index(cls, index, matched_values, page_size=None, before=None, after=None):
    """
    Calls :any:`Index.match` and then works just like :any:`page`.

    :param matched_values:
      Matched value or list of matched values, passed into :any:`Index.match`.
    """
    if not isinstance(matched_values, list):
      matched_values = [matched_values]
    client = index.client
    match_set = index.match(*matched_values)
    getter = Model._index_ref_getter(index)
    return cls._map_page(client, match_set, getter, page_size=page_size, before=before, after=after)

  @classmethod
  def iter_index(cls, index, matched_values, page_size=None):
    """
    Calls :any:`Index.match` and then works just like :any:`iterator`.

    :param matched_values:
      Matched value or list of matched values, passed into :any:`Index.match`.
    :param page_size:
      Size of each page.
    """
    if not isinstance(matched_values, list):
      matched_values = [matched_values]
    client = index.client
    match_set = index.match(*matched_values)

    get = Model._index_ref_getter(index)
    def mapper(instance):
      return cls.get_from_resource(client, instance)
    return Page.set_iterator(client, match_set, page_size=page_size, map_lambda=get, mapper=mapper)

  @classmethod
  def get_from_index(cls, index, *matched_values):
    """
    Returns the first instance matched by the index.

    :param index: :any:`Index`
    :param matched_values: Same as for :any:`Index.match`.
    :return: Instance of this class.
    """
    return cls.get_from_resource(index.client, index.get_single(*matched_values))
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
    """Lambda expression for getting an instance Ref out of a match result."""
    if index.values:
      return lambda arr: query.get(query.select(len(index.values), arr))
    else:
      return query.get

  @classmethod
  def _map_page(cls, client, instance_set, page_lambda, page_size=None, before=None, after=None):
    """
    Creates a query to call `page_lambda` on page data, which should fetch instance data.
    Then maps the result page to create Model instances out of that instance data.
    """
    page_query = query.paginate(instance_set, size=page_size, before=before, after=after)
    map_query = query.map(page_lambda, page_query)
    page = Page.from_raw(client.query(map_query))
    return page.map_data(lambda resource: cls.get_from_resource(client, resource))

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
          decoded = field.codec.decode(encoded)
          self._cache[field_name] = decoded
          return decoded

      def setter(self, value):
        # Clear any previous cached decoded value.
        if field_name in self._cache:
          del self._cache[field_name]
        # Codecs are not guaranteed to have decode(encode(value)) === value.
        # So can't set _cache until getter is called.
        encoded = field.codec.encode(value)
        set_path(field.path, encoded, self._current)

    setattr(cls, field_name, property(getter, setter))
  #endregion
