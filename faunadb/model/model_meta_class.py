from functools import partial

from ..helpers import page_through_query
from ..objects import Ref, Set
from .. import query
from ..query import NoVal
from .field import Field

class ModelMetaClass(type):
  """
  All Model subclasses have some abilities of there own.
  When Fields are assigned to them, they generate getters and setters.

  So in:
    class MyModel(Model):
      x = Field()

  MyModel will have an `x` property with getters and setters.
  If the Field has a Converter, then the properties will convert as well.
  """

  def __init__(self, name, bases, dct):
    # Need to call it `self` or sphynx won't document properties.
    # pylint: disable=bad-mcs-method-argument

    class_name = dct.get("__fauna_class_name__")
    if class_name is not None:
      self.__fauna_class_name__ = class_name

      self.class_ref = Ref("users") if class_name == "users" else Ref("classes", class_name)
      """
      Ref for the class.

      `instance.ref` should be the same as `Ref(instance.__class__.class_ref, instance.id())`.
      """
      self.fields = {}
      """Dict (field_name: field) of all fields assigned to this class."""

      for key, value in dct.items():
        if self._maybe_add_field(key, value):
          del dct[key]

    super(ModelMetaClass, self).__init__(name, bases, dct)

  def __setattr__(cls, key, value):
    if not cls._maybe_add_field(key, value):
      super(ModelMetaClass, cls).__setattr__(key, value)

  def create_class(cls, client):
    """Adds this class to the database."""
    return client.post("classes", {"name": cls.__fauna_class_name__}).resource

  def create_class_index(cls, client):
    """Creates an index for use by cls.list."""
    return client.post("indexes", {
      "name": cls.__fauna_class_name__,
      "source": cls.class_ref,
      "path": "class"
    })

  def get(cls, client, ref):
    """Gets the instance of this class specified by `ref`."""
    return cls._get_from_raw(client, client.get(ref).resource)

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


  def list(cls, client, size, before=NoVal, after=NoVal):
    """
    Lists instances of this class.
    Should have created a class index first (see create_class_index).
    :return: Hash of {"data", "before", "after", "count"}.
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
    page = client.query(q).resource
    page["data"] = [cls._get_from_raw(client, raw) for raw in page["data"]]
    return page

  def list_all_iter(cls, client):
    """Iterates over every instance of the class by calling cls.list until it runs out of pages."""
    return page_through_query(partial(cls.list, client))

  def _maybe_add_field(cls, field_name, field):
    """Add the property to cls.fields if it is a Field."""
    is_field = isinstance(field, Field)
    if is_field:
      cls._add_field(field_name, field)
    return is_field

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
