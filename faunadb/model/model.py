from functools import partial

from ..errors import InvalidQuery, DatabaseError
from ..objects import Ref, Set
from ..page import Page
from .. import query
from ..query import NoVal
from .field import Field


class _ModelMetaClass(type):
  """
  The methods in ModelMetaClass can be called on :any:`Method` classes.
  (On the class. **Not** on its instances.)
  """

  def __init__(self, name, bases, dct):
    # Need to call it `self` or sphynx won't document properties.
    # pylint: disable=bad-mcs-method-argument

    class_name = dct.get("__fauna_class_name__")
    if class_name is not None:
      self.__fauna_class_name__ = class_name

      self.class_ref = Ref("users") if class_name == "users" else Ref("classes", class_name)
      self.fields = {}

      for key, value in dct.items():
        if self._maybe_add_field(key, value):
          del dct[key]

    super(_ModelMetaClass, self).__init__(name, bases, dct)

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
    self.changed_fields = set()

    if data:
      for field_name in self.__class__.fields:
        setattr(self, field_name, data.get(field_name))

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
    self.changed_fields.clear()

  def delete(self):
    """Removes this instance from the database."""
    if self.is_new_instance():
      raise InvalidQuery("Instance does not exist in the database.")
    resource = self.client.delete(self.ref)
    self.ref = None
    self.ts = None
    return resource

  def _create(self):
    """
    Saves this to the database for the first time.

    Sets :any:`ref` and :any:`ts`.
    Calling this will cause :py:meth:`is_new_instance` to be False.
    """
    resource = self.client.post(self.__class__.class_ref, {"data": self}).resource
    self.ref = resource["ref"]
    self.ts = resource["ts"]

  def _replace(self):
    """
    Sends a complete copy of this to the database to update all fields.
    Fails if there is no instance to update. (Use `create()` first.)
    Updates self.ts.
    """
    resource = self.client.put(self.ref, {"data": self}).resource
    if self.ref != resource["ref"]:
      raise DatabaseError("Response ref is different than this instance's.")
    self.ts = resource["ts"]

  def _update(self):
    """
    Updates only the fields that have changed.
    If a concurrent process
    """
    if self.changed_fields:
      changed_values = {field_name: self.get_raw(field_name) for field_name in self.changed_fields}
      resource = self.client.patch(self.ref, {"data": changed_values}).resource
      if self.ref != resource["ref"]:
        raise DatabaseError("Response ref is different than this instance's.")
      self.ts = resource["ts"]
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

  def to_fauna_json(self):
    # pylint: disable=missing-docstring
    dct = {}
    for field_name in self.__class__.fields:
      dct[field_name] = self.get_raw(field_name)
    if self.ref is not None:
      dct["ref"] = self.ref
    return dct

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
  #endregion

  @staticmethod
  def _raw_field_name(field_name):
    """Property name for raw value."""
    return "__raw_" + field_name

  @staticmethod
  def _converted_field_name(field_name):
    """Property name for converted value."""
    return "__converted_" + field_name

  #region Class methods
  @classmethod
  def create_class(cls, client):
    """
    Adds this class to the database.
    This should only be called once.
    Must be called before any instances :py:meth:`save`.
    """
    return client.post("classes", {"name": cls.__fauna_class_name__}).resource

  @classmethod
  def create_class_index(cls, client):
    """
    Creates an index for use by :py:meth:`list`.
    This should only be called once.
    """
    return client.post("indexes", {
      "name": cls.__fauna_class_name__,
      "source": cls.class_ref,
      "path": "class"
    })

  @classmethod
  def get(cls, client, ref):
    """Gets the instance of this class specified by `ref`."""
    return cls._get_from_raw(client, client.get(ref).resource)

  @classmethod
  def list(cls, client, size, before=NoVal, after=NoVal):
    """
    Lists instances of this class.
    Must call :py:meth:`create_class_index` first.

    :return:
      :any:`Page`.
    """
    class_index = Ref("indexes", cls.__fauna_class_name__)
    instances = Set.match(cls.class_ref, class_index)

    get = query.lambda_expr("x", query.get(query.var("x")))
    page = query.paginate(instances, size=size, before=before, after=after)
    v_page = query.var("page")
    q = query.let({"page": page}, query.object(
      before=query.select("before", v_page, default=None),
      after=query.select("after", v_page, default=None),
      data=query.map(get, query.select("data", v_page))
    ))
    page = Page.from_json(client.query(q).resource)
    return page.map_data(partial(cls._get_from_raw, client))

  @classmethod
  def list_all_iter(cls, client):
    """Iterates over every instance of the class by calling :py:meth:`list` repeatedly."""
    return Page.page_through_query(partial(cls.list, client))
  #endregion

  #region Private class methods
  @classmethod
  def _get_from_raw(cls, client, resource):
    """Given raw JSON data, create a class instance."""
    instance = cls(client)
    instance.ref = resource["ref"]
    instance.ts = resource["ts"]

    raw_data = resource if cls.__fauna_class_name__ == "settings" else resource["data"]

    for field_name in cls.fields:
      # pylint: disable=protected-access
      instance._set_raw(field_name, raw_data.get(field_name))

    return instance

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
      # Getting the value just gets or sets the raw value (and updates `changed_fields`).
      def getter(self):
        return self.get_raw(field_name)
      def setter(self, value):
        self._set_raw(field_name, value)
        self.changed_fields.add(field_name)
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
        self.changed_fields.add(field_name)

      setattr(cls, field_name, property(getter, setter))
  #endregion
