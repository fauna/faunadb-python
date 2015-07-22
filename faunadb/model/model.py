from ..errors import InvalidQuery, DatabaseError
from .model_meta_class import ModelMetaClass


class Model(object):
  """
  Base class for all models.
  These classes represent values to be fetched from or sent to the database.
  They are the link between Python classes and FaunaDB classes.
  The basic format is::

    class MyModel(Model):
      __fauna_class_name__ = 'my_models'
      my_field = Field()

  All models have "ref" and "ts" properties, as well as properties for every field specified.
  Give a class fields by assigning new class properties whose values are Fields.
  """

  # Pylint doesn't recognize properties added by ModelMetaClass (class_ref, fields)
  # pylint: disable=no-member

  __metaclass__ = ModelMetaClass

  def __init__(self, client, **data):
    self.client = client
    "Client instance that the model uses to save to the database."
    self.ref = None
    "Ref of this instance in the database. None if this is a new instance."
    self.ts = None
    """
    Timestamp of latest database save.
    None if this is a new instance.
    """
    self.changed_fields = set()
    for field_name in self.__class__.fields:
      setattr(self, field_name, data.get(field_name))

  def id(self):
    """The id portion of this instance's ref."""
    if self.is_new_instance():
      raise InvalidQuery("Instance has not been saved to the database, so no id exists.")
    return self.ref.id()

  #region Persistence
  def is_new_instance(self):
    """
    Whether this instance has ever been saved to the database.
    """
    return self.ref is None

  def save(self, replace=False):
    """
    Saves this instance to the database.
    If this is a new instance, creates it and sets self.ref.
    Otherwise, updates any changed fields.
    :param replace:
    If true, this will update all fields using a "replace" query instead of "update".
    See https://faunadb.com/documentation#queries-write_functions.
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

    Sets self.ref and self.ts.
    Calling this will cause self.is_new_instance() to be False.
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
    return "%s(ref=%s, ts=%s, %s)" % (self.__class__.__name__, self.ref, self.ts, fields)
  #endregion

  #region Conversion
  def to_fauna_json(self):
    # pylint: disable=missing-docstring
    dct = {}
    for field_name in self.__class__.fields:
      dct[field_name] = self.get_raw(field_name)
    if self.ref is not None:
      dct["ref"] = self.ref
    return dct

  def get_raw(self, field_name):
    """
    Gets the value of a field as encoded in json.
    If this instance was created through raw values, simply returns them.
    If this instance was created through converted values,
    this is the result of field.converter.value_to_raw.
    """
    return getattr(self, Model.raw_field_name(field_name))

  def _get_converted(self, field_name):
    """Gets the converted value for a field, or None if that has not been set."""
    return getattr(self, Model.converted_field_name(field_name))

  def _set_raw(self, field_name, value):
    """
    Sets the __raw_xxx hidden field.
    Not safe to call unless __converted_xxx is set to None or to the conversion of the raw value.
    """
    setattr(self, Model.raw_field_name(field_name), value)

  def _set_converted(self, field_name, value):
    """Sets the converted value for a field."""
    setattr(self, Model.converted_field_name(field_name), value)

  def _has_converted(self, field_name):
    """Whether the field has been converted yet."""
    return hasattr(self, Model.converted_field_name(field_name))
  #endregion

  @staticmethod
  def raw_field_name(field_name):
    """Property name for raw value."""
    return "__raw_" + field_name

  @staticmethod
  def converted_field_name(field_name):
    """Property name for converted value."""
    return "__converted_" + field_name
