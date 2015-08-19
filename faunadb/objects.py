"""
Types used in queries and responses.
See https://faunadb.com/documentation#queries-values-special_types.
"""

from .errors import InvalidQuery


class Ref(object):
  """
  FaunaDB ref. See https://faunadb.com/documentation#queries-values.

  A simple wrapper around a string which can be extracted using str(ref).
  Queries that require a Ref will not work if you just pass in a string.
  """

  def __init__(self, class_name, instance_id=None):
    """
    Create a Ref from a string, such as `Ref("databases/prydain")`.
    Can also call `Ref("databases", "prydain")`.
    """
    if instance_id is None:
      self._ref = class_name
    else:
      self._ref = "%s/%s" % (str(class_name), instance_id)

  def to_class(self):
    """
    Gets the class part out of the Ref.
    This is done by removing ref.id().
    So `Ref("a", "b/c").to_class()` will be `Ref("a/b")`.
    """
    if self._ref.startswith("classes"):
      # It looks like "classes/xxx/123", take "classes/xxx"
      _ref = "/".join(self._ref.split("/", 3)[:2])
    else:
      # It looks like "users/123", take "users"
      _ref = self._ref.split("/", 2)[0]
    return Ref(_ref)

  def id(self):
    """
    Removes the class part of the ref, leaving only the id.
    This is everything after the last `/`.
    """
    return self._ref.split("/")[-1]

  def to_fauna_json(self):
    """Wraps it in a @ref hash to be sent as a query."""
    return {"@ref": str(self)}

  def __str__(self):
    return self._ref

  def __repr__(self):
    return "Ref(%s)" % repr(self._ref)

  def __eq__(self, other):
    # pylint: disable=protected-access
    return isinstance(other, Ref) and self._ref == other._ref

  def __ne__(self, other):
    return not self == other


class Set(object):
  """
  FaunaDB Set match. See https://faunadb.com/documentation#queries-sets.
  For constructing sets out of other sets, see set functions in faunadb.query.
  """

  @staticmethod
  def match(match, index):
    """See https://faunadb.com/documentation#queries-sets."""
    return Set({"match": match, "index": index})

  @staticmethod
  def union(sets):
    """See https://faunadb.com/documentation#queries-sets."""
    return Set({"union": sets})

  @staticmethod
  def intersection(sets):
    """See https://faunadb.com/documentation#queries-sets."""
    return Set({"intersection": sets})

  @staticmethod
  def difference(source, sets):
    """See https://faunadb.com/documentation#queries-sets."""
    return Set({"difference": [source] + sets})

  @staticmethod
  def join(source, target):
    """See https://faunadb.com/documentation#queries-sets."""
    return Set({"join": source, "with": target})

  def __init__(self, query_json):
    self.query_json = query_json

  def to_fauna_json(self):
    # pylint: disable=missing-docstring
    return {"@set": self.query_json}

  def __repr__(self):
    return "Set(%s)" % repr(self.query_json)

  def __eq__(self, other):
    return isinstance(other, Set) and self.query_json == other.query_json

  def __ne__(self, other):
    return not self == other


class Event(object):
  """FaunaDB Event. See https://faunadb.com/documentation#queries-values."""

  # pylint: disable=invalid-name
  def __init__(self, ts, action=None, resource=None):
    self.ts = ts
    "Microsecond UNIX timestamp at which the event occurred."
    if action not in (None, "create", "delete"):
      raise InvalidQuery("Action must be create or delete or None.")
    self.action = action
    '"create" or "delete"'
    self.resource = resource
    "The Ref of the affected instance."

  def to_fauna_json(self):
    # pylint: disable=missing-docstring
    dct = {"ts": self.ts, "action": self.action, "resource": self.resource}
    return {k: v for k, v in dct.iteritems() if v is not None}

  def __repr__(self):
    return "Event(ts=%s, action=%s, resource=%s)" % (
      repr(self.ts), repr(self.action), repr(self.resource))

  def __eq__(self, other):
    return isinstance(other, Event) and \
      self.ts == other.ts and \
      self.action == other.action and \
      self.resource == other.resource

  def __ne__(self, other):
    return not self == other
