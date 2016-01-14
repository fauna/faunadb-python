"""
Types used in queries and responses.
See the `docs <https://faunadb.com/documentation/queries#values>`__.
"""
from datetime import datetime
# pylint: disable=redefined-builtin
from builtins import str, object
from iso8601 import parse_date

class Ref(object):
  """
  FaunaDB ref. See the `docs <https://faunadb.com/documentation/queries#values-special_types>`__.

  A simple wrapper around a string which can be extracted using ``ref.value``.
  Queries that require a Ref will not work if you just pass in a string.
  """

  def __init__(self, *parts):
    """
    Create a Ref from a string, such as ``Ref("databases/prydain")``.
    Can also call ``Ref("databases", "prydain")`` or ``Ref(Ref("databases"), "prydain")``.
    """
    self.value = "/".join(str(part) for part in parts)

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


class Set(object):
  """
  FaunaDB Set.
  This represents a set returned as part of a response. This looks like ``{"@set": set_query}``.
  For query sets see :doc:`query`.
  """
  def __init__(self, set_query):
    self.query = set_query

  def to_fauna_json(self):
    return {"@set": self.query}

  def __repr__(self):
    return "Set(%s)" % repr(self.query)

  def __eq__(self, other):
    return isinstance(other, Set) and self.query == other.query

  def __ne__(self, other):
    # pylint: disable=unneeded-not
    return not self == other


class Event(object):
  """FaunaDB Event. See the `docs <https://faunadb.com/documentation/queries#values>`__."""

  @staticmethod
  def from_raw(raw):
    """
    Events are not automatically converted.
    Use this on a dict that you know represents an Event.
    """
    return Event(raw["resource"], raw["ts"], raw["action"])

  # pylint: disable=invalid-name
  def __init__(self, resource, ts, action):
    if action not in ("create", "delete"):
      raise ValueError('Action must be "create" or "delete".')
    self.resource = resource
    """The Ref of the affected instance."""
    self.ts = ts
    "Microsecond UNIX timestamp at which the event occurred."
    self.action = action
    '''"create" or "delete"'''

  def to_fauna_json(self):
    return {"resource": self.resource, "ts": self.ts, "action": self.action}

  def __repr__(self):
    return "Event(resource=%s, ts=%s, action=%s)" % (
      repr(self.resource), repr(self.ts), repr(self.action))

  def __eq__(self, other):
    return isinstance(other, Event) and \
      self.resource == other.resource and \
      self.ts == other.ts and \
      self.action == other.action

  def __ne__(self, other):
    # pylint: disable=unneeded-not
    return not self == other


class FaunaTime(object):
  """
  FaunaDB time. See the `docs <https://faunadb.com/documentation/queries#values-special_types>`__.

  For dates, regular :class:`datetime.date` objects are used.
  """

  def __init__(self, value):
    """
    :param value:
      If a :class:`datetime.datetime` is passed, it is converted to a string.
      Must include an offset.
    """
    if isinstance(value, datetime):
      if datetime.utcoffset is None:
        raise ValueError("FaunaTime requires offset-aware datetimes")
      value = value.isoformat()

    # Convert +00:00 offset to zulu for comparison equality
    # We don't check for +0000 or +00 as they are not valid in FaunaDB
    self.value = value.replace("+00:00", "Z")
    """ISO8601 time string"""

  def to_datetime(self):
    """
    Convert to an offset-aware datetime object.
    This is lossy as datetimes have microsecond rather than nanosecond precision.
    """
    return parse_date(self.value)

  def to_fauna_json(self):
    return {"@ts": self.value}

  def __repr__(self):
    return "FaunaTime(%s)" % repr(self.value)

  def __eq__(self, other):
    return isinstance(other, FaunaTime) and self.value == other.value

  def __ne__(self, other):
    # pylint: disable=unneeded-not
    return not self == other
