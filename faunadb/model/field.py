# TODO: unique, active
class Field(object):
  """Stores information about a field."""
  def __init__(self, converter=None):
    self.converter = converter
