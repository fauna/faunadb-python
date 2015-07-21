"General utilities."

from types import FunctionType

class Spreader(object):
  "Delegates calls to each of self.parrts."

  def __init__(self, parts):
    self.parts = parts

  def __getattr__(self, name):
    "Methods of this class call that same method on self.parts and return nothing."
    def call(*args):
      "Closure around `name` that calls that method on parts."
      for part in self.parts:
        getattr(part, name)(*args)
    return call

def override(superclass):
  """
  Indicates that a method exists to implement or re-implement a method on a superclass.
  If the superclass is passed in, override will check that it actually has that method.
  """
  if isinstance(superclass, FunctionType):
    # @override passed with no args.
    return superclass

  def do_override(method):
    "Checks that the superclass has the method."
    assert method.__name__ in dir(superclass),\
      "No method %s in %s to override." % (method.__name__, superclass)
    return method
  return do_override
