""":any:`Codec` and subclasses."""

from ..errors import InvalidValue

class Codec(object):
  """
  A Codec sits inside a :any:`Field` in a :any:`Model` and prepares data for database storage.

  Encoded values must be JSON data:
  dicts, lists, numbers, strings, and types from :doc:`objects`.

  A field without a Codec must store only JSON data.

  :any:`Model` instances cache the results of conversions.
  """

  def decode(self, raw, model):
    """
    Converts a value from the database into a python object.

    The value taken from the database will already have types from faunadb.objects converted.
    """
    raise NotImplementedError

  def encode(self, value, model):
    """
    Converts a value to prepare for storage in the database.
    The encoded value may contain objects with `to_fauna` implemented.
    """
    raise NotImplementedError


class RefCodec(Codec):
  """
  Uses a :any:`Ref` as the decoded value and :samp:`{"@ref": string}` JSON as the encoded value.

  To reference a member of a class that hasn't been defined yet
  (including the current class), assign the field after the class has been defined::

    class MyModel(Model):
      __fauna_class_name__ = 'my_models'
      plain_field = Field()
    MyModel.reference_field = Field(RefCodec(MyModel))

  If the ref is invalid, :any:`errors.NotFound` will be thrown.
  """

  def __init__(self, referenced_model_class):
    self.referenced_model_class = referenced_model_class
    """The subclass of :any:`Model` to be referenced."""

  def encode(self, value, model):
    """Gets the :any:`Ref` for a :any:`Model`."""
    if value is None:
      return None
    if value.is_new_instance():
      raise InvalidValue("The referenced instance must be saved to the database first.")
    if not isinstance(value, self.referenced_model_class):
      raise InvalidValue(
        "The reference should be a %s; got a %s." % (self.referenced_model_class, value.__class__))
    return value.ref

  def decode(self, raw, model):
    """Fetches the data for a :any:`Ref` and creates a :any:`Model`."""
    if raw is None:
      return None
    return self.referenced_model_class.get(model.client, raw)
