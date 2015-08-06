"""Converter and common Converter subclasses."""

from ..errors import InvalidValue


class Converter(object):
  """
  A Converter sits inside a Field in a Model and prepares data for database storage.
  A field without a Converter should only store JSON-compatible data:
  dicts, lists, numbers, strings, and types from faunadb.objects.
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
  Uses Refs as raw values and model instances as converted values.
  If you want to reference a member of a class that hasn't been defined yet
  (including the current class) you assign the field after the class has been defined::

    class MyModel(Model):
      __fauna_class_name__ = 'my_models'
      plain_field = Field()
    MyModel.reference_field = Field(RefConverter(MyModel))
  """

  def __init__(self, referenced_model_class, nullable=False):
    """
    :param referenced_class: A subclass of Model.
    :param nullable: Whether it's OK for the reference to be missing.
    """
    self.referenced_model_class = referenced_model_class
    self.nullable = nullable

  def value_to_raw(self, value, model):
    """Gets the Ref for a model instance."""
    if value is None:
      if not self.nullable:
        raise InvalidValue("The reference must exist.")
      return None
    if value.is_new_instance():
      raise InvalidValue("The referenced instance must be saved to the database first.")
    return value.ref

  def raw_to_value(self, raw, model):
    """Fetches the data for a Ref and creates a Model instance."""
    if raw is None:
      if not self.nullable:
        InvalidValue("The reference must exist.")
      return None
    return self.referenced_model_class.get(model.client, raw)
