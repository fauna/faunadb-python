"""
Types used in queries and responses.
See https://faunadb.com/documentation#queries-values-special_types.
"""

from .errors import InvalidQuery
from ._util import override


class Ref(object):
  """
  FaunaDB ref. See http://localhost:3000/documentation#queries-values.

  A simple wrapper around a string which can be extracted using str(ref).
  Queries that require a Ref will not work if you just pass in a string.
  """

  def __init__(self, class_name, instance_id=""):
    """
    Create a Ref from a string, such as `Ref("databases/prydain")`.
    Can also call `Ref("databases", "prydain")`.
    """
    self._ref_str = str(class_name) + instance_id

  def to_class(self):
    """
    Gets the class part out of the Ref.
    This is done by removing ref.id().
    So `Ref("a", "b/c").to_class()` will be `Ref("a/b")`.
    """

    if self._ref_str.startswith("classes"):
      # It looks like "classes/xxx/123", take "classes/xxx"
      return Ref(self._ref_str.split('/', 3)[0:2].join('/'))
    else:
      # It looks like "users/123", take "users"
      return Ref(self._ref_str.split('/', 2)[0])

  def id(self):
    """
    Removes the class part of the ref, leaving only the id.
    This is everything after the last `/`.
    """
    return self._ref_str.split('/')[-1]

  @override
  def to_fauna_json(self):
    "Wraps it in a @ref hash to be sent as a query."
    return {"@ref": str(self)}

  @override
  def __str__(self):
    return self._ref_str

  @override
  def __repr__(self):
    return "Ref(%s)" % repr(self._ref_str)

  @override
  def __eq__(self, other):
    # pylint: disable=protected-access
    return isinstance(other, Ref) and self._ref_str == other._ref_str

  @override
  def __ne__(self, other):
    return not self == other


class Set(object):
  """
  FaunaDB Set match. See https://faunadb.com/documentation#queries-sets.
  For constructing sets out of other sets, see set functions in faunadb.query.
  """

  def __init__(self, match, index):
    self.match = match
    self.index = index

  @override
  def to_fauna_json(self):
    # pylint: disable=missing-docstring
    return {"@set": {"match": self.match, "index": self.index}}

  @override
  def __str__(self):
    return "Set(%s, %s)" % (str(self.match), str(self.index))

  @override
  def __repr__(self):
    return "Set(%s, %s)" % (repr(self.match), repr(self.index))

  @override
  def __eq__(self, other):
    return isinstance(other, Set) and self.match == other.match and self.index == other.index

  @override
  def __ne__(self, other):
    return not self == other


class Event(object):
  "FaunaDB Event. See http://localhost:3000/documentation#queries-values."

  # pylint: disable=invalid-name
  def __init__(self, ts, action=None, resource=None):
    self.ts = ts
    "Microsecond UNIX timestamp at which the event occurred."
    if action not in {None, "create", "delete"}:
      raise InvalidQuery("Action must be create or delete or None.")
    self.action = action
    '"create" or "delete"'
    self.resource = resource
    "The Ref of the affected instance."

  @override
  def to_fauna_json(self):
    # pylint: disable=missing-docstring
    dct = {"ts": self.ts, "action": self.action, "resource": self.resource}
    return {k: v for k, v in dct.iteritems() if v is not None}

  @override
  def __str__(self):
    return "Event(ts=%s, action=%s, resource=%s)" % (self.ts, self.action, self.resource)

  @override
  def __eq__(self, other):
    return isinstance(other, Event) and \
      self.ts == other.ts and \
      self.action == other.action and \
      self.resource == other.resource

  @override
  def __ne__(self, other):
    return not self == other
