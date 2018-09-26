from faunadb import query

class Page(object):
  """
  Represents a single pagination result.
  See ``paginate`` in the `docs <https://app.fauna.com/documentation/reference/queryapi#read-functions>`__.
  You must convert to Page yourself using :py:meth:`from_raw`.
  """

  @staticmethod
  def from_raw(raw):
    """Convert a raw response dict to a Page."""
    return Page(raw["data"], raw.get("before"), raw.get("after"))

  def __init__(self, data, before=None, after=None):
    self.data = data
    """List of elements returned by the query."""
    self.before = before
    """Optional :any:`Ref` for an instance that comes before this page."""
    self.after = after
    """Optional :any:`Ref` for an instance that comes after this page."""

  def map_data(self, func):
    """Return a new Page whose data has had ``func`` applied to each element."""
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
      If present, a :any:`lambda_` for mapping set elements.
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
        queried = query.map_(map_lambda, queried)
      return Page.from_raw(client.query(queried))

    page = get_page(size=page_size)
    for val in page.data:
      yield val if mapper is None else mapper(val)

    next_cursor = "after" if page.after is not None else "before"

    while getattr(page, next_cursor) is not None:
      page = get_page(**{"size": page_size, next_cursor: getattr(page, next_cursor)})
      for val in page.data:
        yield val if mapper is None else mapper(val)
