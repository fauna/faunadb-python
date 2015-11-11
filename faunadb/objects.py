"""
Types used in queries and responses.
See the `docs <https://faunadb.com/documentation/queries#values>`__.
"""

from .errors import InvalidQuery, InvalidValue
from . import query
from ._util import no_null_values

class Ref(object):
  """
  FaunaDB ref. See the `docs <https://faunadb.com/documentation/queries#values-special_types>`__.

  A simple wrapper around a string which can be extracted using :samp:`ref.value`.
  Queries that require a Ref will not work if you just pass in a string.
  """

  def __init__(self, *parts):
    """
    Create a Ref from a string, such as :samp:`Ref("databases/prydain")`.
    Can also call :samp:`Ref("databases", "prydain")` or :samp:`Ref(Ref("databases"), "prydain")`.
    """
    self.value = "/".join(str(part) for part in parts)

  def to_class(self):
    """
    Gets the class part out of the Ref.
    This is done by removing the id.
    So :samp:`Ref("a", "b/c").to_class()` will be :samp:`Ref("a/b")`.
    """
    parts = self.value.split("/")
    if len(parts) == 1:
      return self
    else:
      return Ref(*parts[:-1])

  def id(self):
    """
    Removes the class part of the Ref, leaving only the id.
    This is everything after the last :samp:`/`.
    """
    parts = self.value.split("/")
    if len(parts) == 1:
      raise InvalidValue("The Ref does not have an id.")
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
    return not self == other


class Set(object):
  """
  FaunaDB Set.
  This represents a set returned as part of a response. This looks like :samp:`{"@set": set_query}`.
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
    return not self == other


class Event(object):
  """FaunaDB Event. See the `docs <https://faunadb.com/documentation/queries#values>`__."""

  @staticmethod
  def from_raw(raw):
    """
    Events are not automatically converted.
    Use this on a dict that you know represents an Event.
    """
    return Event(raw["ts"], raw["action"], raw["resource"])

  # pylint: disable=invalid-name
  def __init__(self, ts, action=None, resource=None):
    self.ts = ts
    "Microsecond UNIX timestamp at which the event occurred."
    if action not in (None, "create", "delete"):
      raise InvalidQuery("Action must be create or delete or None.")
    self.action = action
    """"create" or "delete"""""
    self.resource = resource
    "The Ref of the affected instance."

  def to_fauna_json(self):
    return no_null_values({"ts": self.ts, "action": self.action, "resource": self.resource})

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


class Page(object):
  """
  A single pagination result.
  See :samp:`paginate` in the `docs <https://faunadb.com/documentation/queries#read_functions>`__.
  """

  @staticmethod
  def from_raw(raw):
    return Page(raw["data"], raw.get("before"), raw.get("after"))

  def __init__(self, data, before=None, after=None):
    self.data = data
    """
    Always a list.
    Elements could be raw data; some methods (such as :doc:`model` :py:meth:`list`) convert data.
    """
    self.before = before
    """Optional :any:`Ref` for an instance that comes before this page."""
    self.after = after
    """Optional :any:`Ref` for an instance that comes after this page."""

  def map_data(self, func):
    """Return a new Page whose data has had :samp:`func` applied to each element."""
    return Page([func(x) for x in self.data], self.before, self.after)

  def __repr__(self):
    return "Page(data=%s, before=%s, after=%s)" % (self.data, self.before, self.after)

  def __eq__(self, other):
    return isinstance(other, Page) and\
      self.data == other.data and\
      self.before == other.before and\
      self.after == other.after

  @staticmethod
  def set_iterator(client, set_query, map_lambda=None, mapper=None, page_size=None):
    """
    Iterator that keeps getting new pages of a set.

    :param map_lambda:
      If present, a :any:`lambda_expr` for mapping set elements.
    :param mapper:
      Mapping Python function used on each page element.
    :param page_size:
      Number of instances to be fetched at a time.
    :return:
      Iterator through all elements in the set.
    """

    def get_page(**kwargs):
      queried = query.paginate(set_query, **kwargs)
      if map_lambda is not None:
        queried = query.map(map_lambda, queried)
      return Page.from_raw(client.query(queried))

    page = get_page(size=page_size)
    for val in page.data:
      yield val if mapper is None else mapper(val)

    next_cursor = "after" if page.after is not None else "before"

    while getattr(page, next_cursor) is not None:
      page = get_page(**{"size": page_size, next_cursor: getattr(page, next_cursor)})
      for val in page.data:
        yield val if mapper is None else mapper(val)
