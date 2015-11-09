""":any:`Codec` and subclasses."""

from ..errors import InvalidValue
from ..objects import Ref

class Codec(object):
  """
  A Codec sits inside a :any:`Field` in a :any:`Model` and prepares data for database storage.

  Encoded values must be JSON data:
  dicts, lists, numbers, strings, :any:`Ref` and :any:`Set`.

  A field without a Codec must store only JSON data.

  Input data may be sanitized (e.g. RefCodec converts strings to Refs),
  so there is no guarantee that :samp:`codec.decode(codec.encode(value)) == value`.

  :any:`Model` instances cache the results of conversions.
  """

  def decode(self, raw):
    """
    Converts a value from the database into a python object.

    (The value taken from the database will already have :any:`Ref` or :any:`Set` values converted.)
    """
    raise NotImplementedError

  def encode(self, value):
    """
    Converts a value to prepare for storage in the database.
    The encoded value may contain objects with `to_fauna` implemented.
    """
    raise NotImplementedError


class _RefCodecClass(Codec):
  def decode(self, ref):
    return ref

  def encode(self, value):
    if value is None:
      return None
    elif isinstance(value, str):
      return Ref(value)
    elif isinstance(value, Ref):
      return value
    else:
      raise InvalidValue("Expected a Ref, got: %s" % value)


RefCodec = _RefCodecClass()
"""
Codec for a field whose value is always a :any:`Ref`.
Also converts any strings coming in to Refs.
"""
