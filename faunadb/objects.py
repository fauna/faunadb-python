"""
Types used in queries and responses.
See the `docs <https://fauna.com/documentation/queries#values>`__.
"""
# pylint: disable=redefined-builtin
from builtins import str
from iso8601 import parse_date
from faunadb.query import _Expr

class Ref(_Expr):
  """
  FaunaDB ref. See the `docs <https://fauna.com/documentation/queries#values-special_types>`__.

  A simple wrapper around a string which can be extracted using ``ref.value``.
  Queries that require a Ref will not work if you just pass in a string.
  """

  def __init__(self, *parts):
    """
    Create a Ref from a string, such as ``Ref("databases/prydain")``.
    Can also call ``Ref("databases", "prydain")`` or ``Ref(Ref("databases"), "prydain")``.
    """
    parts_str = "/".join(str(part) for part in parts)

    super(Ref, self).__init__(parts_str)

  def to_class(self):
    """
    Gets the class part out of the Ref.
    This is done by removing the id.
    So ``Ref("a", "b/c").to_class()`` will be ``Ref("a/b")``.
    """
    parts = self.value.split("/")
    if len(parts) == 1:
      return self
    else:
      return Ref(*parts[:-1])

  def id(self):
    """
    Removes the class part of the Ref, leaving only the id.
    This is everything after the last ``/``.
    """
    parts = self.value.split("/")
    if len(parts) == 1:
      raise ValueError("The Ref does not have an id.")
    return parts[-1]

  def to_fauna_json(self):
    return {"@ref": self.value}

  def __str__(self):
    return self.value

  def __repr__(self):
    return "Ref(%s)" % repr(self.value)

  def __eq__(self, other):
    return isinstance(other, Ref) and self.value == other.value

  def __ne__(self, other):
    # pylint: disable=unneeded-not
    return not self == other


class SetRef(_Expr):
  """
  FaunaDB Set.
  This represents a set returned as part of a response.
  For query sets see :doc:`query`.
  """

  def __init__(self, set_ref):
    if isinstance(set_ref, _Expr):
      value = set_ref.value
    else:
      value = set_ref

    super(SetRef, self).__init__(value)

  def to_fauna_json(self):
    return {"@set": self.value}

  def __repr__(self):
    return "SetRef(%s)" % repr(self.value)

  def __eq__(self, other):
    return isinstance(other, SetRef) and self.value == other.value

  def __ne__(self, other):
    # pylint: disable=unneeded-not
    return not self == other
