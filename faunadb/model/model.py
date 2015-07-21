from ..errors import InvalidQuery, DatabaseError
from .._util import override
from .model_meta_class import ModelMetaClass
from ._util import converted_field_name, raw_field_name

class Model(object):
  """
  Base class for all models.
  These classes represent values to be fetched from or sent to the database.
  They are the link between Python classes and FaunaDB classes.
  The basic format is:

    class MyModel(Model):
      __fauna_class_name__ = 'my_models'
      my_field = Field()

  All models have `ref` and `ts` properties, as well as properties for every field specified.
  Give a class fields by assigning new class properties whose values are `Field`s.
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
    if data:
      for field_name in self.__class__.fields:
        setattr(self, field_name, data.get(field_name))

  def id(self):
    "The id portion of this instance's ref."
    if self.is_new_instance():
      raise InvalidQuery("Instance has not been saved to the database, so no id exists.")
    return self.ref.id()

  #region Persistence
  def is_new_instance(self):
    """
    Whether this instance has ever been saved to the database.
    """
    return self.ref is None

  def create(self):
    """
    Saves this to the database for the first time.

    Sets self.ref and self.ts.
    Calling this will cause self.is_new_instance() to be False.
    """
    if not self.is_new_instance():
      raise InvalidQuery("Record has already been saved to the database. Use `update`.")
    response = self.client.post(self.__class__.class_ref, {"data": self})
    self.ref = response["ref"]
    self.ts = response["ts"]

  def update(self):
    """
    Sends a complete copy of this to the database to update all fields.
    Fails if there is no instance to update. (Use `create()` first.)
    Updates self.ts.
    """
    if self.is_new_instance():
      raise InvalidQuery("Record does not yet exist in the database. Use `create`.")
    response = self.client.put(self.ref, {"data": self})
    if self.ref != response["ref"]:
      raise DatabaseError("Response ref is different than this instance's.")
    self.ts = response["ts"]

  def patch(self, **patched_fields):
    """
    Updates several fields and saves the changes to the database.
    It is not recommended to call "patch" if you are possibly changing other values as well.
    """

    for field_name, value in patched_fields.iteritems():
      setattr(self, field_name, value)
    self.do_patch(*patched_fields.iterkeys())

  def do_patch(self, *patched_field_names):
    """
    Sends new values for `patched_field_names` to the database.
    Does not update any other values.
    This can be dangerous if `patched_field_names` does not contain every changed value,
    so it is usually better to call `patch()`.
    """

    if self.is_new_instance():
      raise InvalidQuery("Record does not yet exist in the database.")

    patch_dict = {field_name: self.get_raw(field_name) for field_name in patched_field_names}

    response = self.client.patch(self.ref, {"data": patch_dict})
    if self.ref != response["ref"]:
      raise DatabaseError("Response ref is different than this instance's.")
    self.ts = response["ts"]

  def delete(self):
    "Removes this instance from the database."
    if self.is_new_instance():
      raise InvalidQuery("Record does not exist in the database.")
    response = self.client.delete(self.ref)
    self.ref = None
    self.ts = None
    return response
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
  @override
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
    return getattr(self, raw_field_name(field_name))

  def _get_converted(self, field_name):
    "Gets the converted value for a field, or None if that has not been set."
    return getattr(self, converted_field_name(field_name))

  def _set_raw(self, field_name, value):
    """
    Sets the __raw_xxx hidden field.
    Not safe to call unless __converted_xxx is set to None or to the conversion of the raw value.
    """
    setattr(self, raw_field_name(field_name), value)

  def _set_converted(self, field_name, value):
    "Sets the converted value for a field."
    setattr(self, converted_field_name(field_name), value)
  #endregion

