from functools import partial

from ..errors import InvalidQuery, InvalidValue, DatabaseError
from ..objects import Ref
from ..page import Page
from .. import query
from ..query import NoVal
from .field import Field

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
    # Fields can be added evem after the class has been defined.
    MyModel.other_field = Field()

  Properties will be generated for each :any:`Field`.

  :samp:`__fauna_class_name__` is mandatory; otherwise this will be treated as an abstract class.

  :any:`Class` :py:meth:`create_for_model` must be called before you can use the model.
  """

  __metaclass__ = _ModelMetaClass

  # These fields are filled in by _ModelMetaClass, but write them here so
  # we can document them and PyLint doesn't give us no-member errors.
  __fauna_class_name__ = None

  #: :any:`Ref` for the class itself.
  #:
  #: :samp:`instance.ref` should be the same as
  #: :samp:`Ref(instance.__class__.class_ref, instance.id())`.
  class_ref = None

  #: Dict {field_name: :any:`Field`} of all fields assigned to this class.
  fields = None
  builtin_fields = {}

  def __init__(self, client, **data):
    self.client = client
    """Client instance that the model uses to save to the database."""
    self.ref = None
    """:any:`Ref` of this instance in the database. :samp:`None` iff :py:meth:`is_new_instance`."""
    self.ts = None
    """
    Microsecond UNIX Timestamp of latest :py:meth:`save`.
    :samp:`None` iff :py:meth:`is_new_instance`.
    """
    self._changed_fields = set()

    cls = self.__class__
    if data:
      for field_name in cls.fields:
        setattr(self, field_name, data.get(field_name))
      for field_name in data:
        if not field_name in cls.fields:
          raise InvalidValue("Unrecognized field %s" % field_name)

  def id(self):
    """The id portion of this instance's :any:`Ref`."""
    if self.is_new_instance():
      raise InvalidQuery("Instance has not been saved to the database, so no id exists.")
    return self.ref.id()

  #region Persistence
  def is_new_instance(self):
    """
    :samp:`False` if this has ever been saved to the database.
    Iff :samp:`True`, :any:`ref` and :any:`ts` will be :samp:`None`.
    """
    return self.ref is None

  def save(self, replace=False):
    """
    Saves this instance to the database.

    If :py:meth:`is_new_instance`, creates it and sets :any:`ref` and :any:`ts`.
    Otherwise, updates any changed fields.

    :param replace:
      If true, this will update all fields using a :samp:`replace` query instead of :samp:`update`.
      See the `docs <https://faunadb.com/documentation#queries-write_functions>`_.
    """
    if self.is_new_instance():
      self._create()
    elif replace:
      self._replace()
    else:
      self._update()
    self._changed_fields.clear()

  def delete(self):
    """Removes this instance from the database."""
    if self.is_new_instance():
      raise InvalidQuery("Instance does not exist in the database.")
    self.client.delete(self.ref)
    self.ref = None
    self.ts = None

  def _create(self):
    """
    Saves this to the database for the first time.

    Sets :any:`ref` and :any:`ts`.
    Calling this will cause :py:meth:`is_new_instance` to be False.
    """
    cls = self.__class__
    resource = self.client.post(cls.class_ref, self._data_json()).resource
    self.ref = resource["ref"]
    self.ts = resource["ts"]
    # Builtin fields may get set by faunadb upon instance creation.
    for field_name in cls.builtin_fields:
      self._set_raw(field_name, resource.get(field_name))

  def _replace(self):
    """
    Sends a complete copy of this to the database to update all fields.
    Fails if there is no instance to update. (Use `create()` first.)
    Updates self.ts.
    """
    resource = self.client.put(self.ref, self._data_json()).resource
    if self.ref != resource["ref"]:
      raise DatabaseError("Response ref is different than this instance's.")
    self.ts = resource["ts"]

  def _update(self):
    """
    Updates only the fields that have changed.
    If a concurrent process
    """
    if self._changed_fields:
      changed_values = self._changed_values()
      resource = self.client.patch(self.ref, changed_values).resource
      if self.ref != resource["ref"]:
        raise DatabaseError("Response ref is different than this instance's.")
      self.ts = resource["ts"]

  def _changed_values(self):
    values = {}
    data = {}
    cls = self.__class__
    for field_name in self._changed_fields:
      raw = self.get_raw(field_name)
      (values if field_name in cls.builtin_fields else data)[field_name] = raw
    if data:
      values["data"] = data
    return values

  def _data_json(self):
    dct = {}
    data = {}

    cls = self.__class__
    for field_name in cls.fields:
      raw = self.get_raw(field_name)
      # KLUDGE (this will make 'replace' not work...)
      if not (self.is_new_instance() and raw is None):
        (dct if field_name in cls.builtin_fields else data)[field_name] = raw

    if data:
      dct["data"] = data
    return dct
  #endregion

  #region Standard methods
  def __eq__(self, other):
    """
    By default, Model instances are considered equal iff
    they have the same ref, ts, and field values.
    """
    if self is other:
      return True
    if not (other.__class__ == self.__class__ and self.ref == other.ref and self.ts == other.ts):
      return False
    for field_name in self.__class__.fields:
      if getattr(self, field_name) != getattr(other, field_name):
        return False
    return True

  def __ne__(self, other):
    return not self == other

  def __repr__(self):
    fields = [field + "=" + str(getattr(self, field)) for field in self.__class__.fields]
    return "%s(ref=%s, ts=%s, %s)" % (self.__class__.__name__, self.ref, self.ts, ', '.join(fields))
  #endregion

  #region Conversion
  def get_raw(self, field_name):
    """
    Gets the value of a field as directly returned from the database.
    For fields with no :any:`Converter`, this is the same as the usual value.

    If this class was initialized with converted values
    (rather than fetching raw values from the database),
    this will call :samp:`field.converter.value_to_raw` on each :any:`Field` with a converter
    and cache the result.
    """
    return getattr(self, Model._raw_field_name(field_name))

  def _get_converted(self, field_name):
    """
    Gets the converted value for a field.
    For fields with no converter, this just gets the raw value.

    If this class was initialized with converted values, the field will already be set.
    Otherwise, this will call :samp:`field.converter.raw_to_value`
    on each :any`Field` with a converter and cache the result.
    """
    return getattr(self, Model._converted_field_name(field_name))

  def _set_raw(self, field_name, value):
    """
    Sets the __raw_xxx hidden field.
    Not safe to call unless __converted_xxx is set to None or to the conversion of the raw value.
    """
    setattr(self, Model._raw_field_name(field_name), value)

  def _set_converted(self, field_name, value):
    """Sets the converted value for a field."""
    setattr(self, Model._converted_field_name(field_name), value)

  def _has_converted(self, field_name):
    """Whether the field has been converted yet."""
    return hasattr(self, Model._converted_field_name(field_name))

  @staticmethod
  def _raw_field_name(field_name):
    """Property name for raw value."""
    return "__raw_" + field_name

  @staticmethod
  def _converted_field_name(field_name):
    """Property name for converted value."""
    return "__converted_" + field_name
  #endregion

  #region Class methods
  @classmethod
  def is_abstract(cls):
    """A Model class is considered abstract if __fauna_class_name__ is not set."""
    return cls.__fauna_class_name__ is None

  @classmethod
  def get(cls, client, ref):
    """Gets the instance of this class specified by :samp:`ref`."""
    return cls._get_from_raw(client, client.get(ref).resource)

  @classmethod
  def get_by_id(cls, client, id):
    """Gets the instance of this class specified by :samp:`id`."""
    return cls.get(client, Ref(cls.class_ref, id))

  @classmethod
  def create(cls, client, *args, **kwargs):
    c = cls(client, *args, **kwargs)
    c._create()
    return c

  @classmethod
  def page(cls, client, instance_set, size=NoVal, before=NoVal, after=NoVal):
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
    return cls._convert_page_data(client, instance_set, get, size, before, after)

  @classmethod
  def _convert_page_data(cls, client, query_set, instance_get_lambda, size, before, after):
    """
    Run a query, converting page data to model instances.
    instance_get_lambda is a query lambda whose result is data for an instance.
    """
    page = query.paginate(query_set, size=size, before=before, after=after)
    v_page = query.var("page")
    q = query.let({"page": page}, query.object(
      before=query.select("before", v_page, default=None),
      after=query.select("after", v_page, default=None),
      data=query.map(instance_get_lambda, query.select("data", v_page))
    ))
    page = Page.from_json(client.query(q).resource)
    return page.map_data(partial(cls._get_from_raw, client))

  @classmethod
  def page_index(cls, index, matched_values, size=NoVal, before=NoVal, after=NoVal):
    """
    Calls :any:`Index` :py:meth:`match` and then works just like :py:meth:`page`.

    :param matched_values:
      Value or values to match the index's :samp:`terms`.
    """
    if not isinstance(matched_values, list):
      matched_values = [matched_values]
    match_set = index.match(*matched_values)

    client = index.client
    if index.values:
      # Page data entries look like [value, value, ..., ref], so select the "ref" and get that.
      get = query.lambda_expr("arr", query.get(query.select(len(index.values), query.var("arr"))))
      return cls._convert_page_data(client, match_set, get, size, before, after)
    else:
      return cls.page(client, match_set, size=size, before=before, after=after)

  @classmethod
  def page_iter(cls, client, instance_set):
    """
    Returns an iterator of model instances.
    :samp:`instance_set` should be a Set describing instances of this class.
    Queries the set repeatedly, converting data to model instances.
    """
    return Page.page_through_query(partial(cls.page, client, instance_set))

  @classmethod
  def iter_index(cls, index, matched_values):
    """
    Calls :py:meth:`match` on the index and iterates through the results with :py:meth:`page_iter`.
    """
    return Page.page_through_query(partial(cls.page_index, index, matched_values))
  #endregion

  #region Private class methods
  @classmethod
  def _get_from_raw(cls, client, resource):
    """Given raw JSON data, create a class instance."""
    instance = cls(client)
    instance.ref = resource["ref"]
    instance.ts = resource["ts"]
    cls._set_fields_from_resource(instance, resource)
    return instance

  @classmethod
  def _set_fields_from_resource(cls, instance, resource):
    raw_data = resource.get("data", {})

    for field_name in cls.fields:
      # pylint: disable=protected-access
      raw = (resource if field_name in cls.builtin_fields else raw_data).get(field_name)
      instance._set_raw(field_name, raw)

  @classmethod
  def _maybe_add_field(cls, field_name, field):
    """Add the property to cls.fields if it is a Field."""
    is_field = isinstance(field, Field)
    if is_field:
      cls._add_field(field_name, field)
    return is_field

  @classmethod
  def _add_field(cls, field_name, field):
    """Add the field to cls.fields and generate a getter and setter."""
    # pylint: disable=missing-docstring, protected-access

    if field_name in ("ref", "ts"):
      raise RuntimeError("Forbidden field name.")

    cls.fields[field_name] = field
    if field.converter is None:
      # There is no converter.
      # Raw value can be set directly.
      # Getting the value just gets or sets the raw value (and updates `_changed_fields`).
      def getter(self):
        return self.get_raw(field_name)
      def setter(self, value):
        self._set_raw(field_name, value)
        self._changed_fields.add(field_name)

      setattr(cls, field_name, property(getter, setter))

    else:
      # Getting the value involves converting it.
      # We store _raw_ and _converted_ fields for the field and use a getter/setter pair.

      # We lazily convert values from raw.
      # This means that e.g. a ref field that is never accessed is never fetched.
      def getter(self):
        # Converting raw->value is done lazily.
        if self._has_converted(field_name):
          # There is a cached converted value.
          return self._get_converted(field_name)
        else:
          # Convert and cache.
          converted = field.converter.raw_to_value(self.get_raw(field_name), self)
          self._set_converted(field_name, converted)
          return converted

      def setter(self, value):
        # Converting value->raw is done eagerly.
        self._set_raw(field_name, field.converter.value_to_raw(value, self))
        self._set_converted(field_name, value)
        self._changed_fields.add(field_name)

      setattr(cls, field_name, property(getter, setter))
  #endregion
