""":any:`Converter` and subclasses."""

from ..errors import InvalidValue


class Converter(object):
  """
  A Converter sits inside a :any:`Field` in a :any:`Model` and prepares data for database storage.

  A Field without a Converter should only store JSON-compatible data:
  dicts, lists, numbers, strings, and types from :doc:`objects`.

  The "raw" value refers to this JSON-compatible data.
  The "value" is what this is converted to and from.

  :any:`Model` instances cache the results of conversions.
  """

  def raw_to_value(self, raw, model):
    """
    Converts a value from the database into a converted value.

    The value taken from the database will already have types from faunadb.objects converted.
    """
    raise NotImplementedError

  def value_to_raw(self, value, model):
    """
    Converts a value to prepare for storage in the database.
    The "raw" value may contain objects with `to_fauna` implemented.
    """
    raise NotImplementedError


class RefConverter(Converter):
  """
  Uses a :any:`Ref` as the raw value and a model instance as the converted value.

  To reference a member of a class that hasn't been defined yet
  (including the current class), assign the field after the class has been defined::

    class MyModel(Model):
      __fauna_class_name__ = 'my_models'
      plain_field = Field()
    MyModel.reference_field = Field(RefConverter(MyModel))
  """

  def __init__(self, referenced_model_class, nullable=False):
    self.referenced_model_class = referenced_model_class
    """The subclass of :any:`Model` to be referenced."""
    self.nullable = nullable
    """
    If true, when the ref is None the converted value will be None as well.
    If false, this will result in an error.
    """

  def value_to_raw(self, value, model):
    """Gets the :any:`Ref` for a :any:`Model`."""
    if value is None:
      if not self.nullable:
        raise InvalidValue("The reference must exist.")
      return None
    if value.is_new_instance():
      raise InvalidValue("The referenced instance must be saved to the database first.")
    return value.ref

  def raw_to_value(self, raw, model):
    """Fetches the data for a :any:`Ref` and creates a :any:`Model`."""
    if raw is None:
      if not self.nullable:
        InvalidValue("The reference must exist.")
      return None
    return self.referenced_model_class.get(model.client, raw)
