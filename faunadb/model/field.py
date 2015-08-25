class Field(object):
  """
  Stores information about a field in a :any:`Model`.
  Fields are stored per-class, not per-instance, so they should be immutable.
  """
  def __init__(self, converter=None):
    self.converter = converter
    """Optional :any:`Converter` for values stored in this field."""
