class Field(object):
  """
  Stores information about a field in a :any:`Model`.
  A Field corresponds to an entry in the :samp:`data` dict for the database instance.
  When you define::

    class MyModel(Model):
      ...
      x = Field()

  :samp:`MyModel` instances will have an :samp:`x` property,
  and instances in the database will have :samp:`data.x` written to on saves.

  A Field can have a :any:`Codec` to translate between database values and Python values.

  Fields are stored per-class, not per-instance, so they should be immutable.
  """
  def __init__(self, codec=None, path=None):
    self.codec = codec
    """Optional :any:`Codec` for values stored in this field."""
    self.path = path
    """
    Path to the field in the FaunaDB instance.
    By default this will be ["data", field_name].
    You could also use a more nested field.
    FaunaDB will not let you create new fields outside of "data"; those are reserved for builtins.
    """
