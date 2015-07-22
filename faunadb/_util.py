"General utilities."

class Spreader(object):
  """Delegates calls to each of self.parts."""
  def __init__(self, parts):
    self.parts = parts

  def __getattr__(self, name):
    """Methods of this class call that same method on self.parts and return nothing."""
    def call(*args):
      """Closure around `name` that calls that method on parts."""
      for part in self.parts:
        getattr(part, name)(*args)
    return call
