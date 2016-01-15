from faunadb import query

class Page(object):
  """
  Represents a single pagination result.
  See ``paginate`` in the `docs <https://faunadb.com/documentation/queries#read_functions>`__.
  You must convert to Page yourself using :py:meth:`from_raw`.
  """

  @staticmethod
  def from_raw(raw):
    """Convert a raw response dict to a Page."""
    return Page(raw["data"], raw.get("before"), raw.get("after"))

  def __init__(self, data, before=None, after=None):
    self.data = data
    """
    Always a list.
    Elements could be raw data; some methods (such as :any:`Model.page`) convert data.
    """
    self.before = before
    """Nullable cursor for the previous page."""
    self.after = after
    """Nullable cursor for the next page."""

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

  def __ne__(self, other):
    # pylint: disable=unneeded-not
    return not self == other

  @staticmethod
  def page_iterator(client, set_query, mapper=None, page_size=None):
    """Like :py:meth:`set_iterator` but iterates over pages rather than their content."""
    def get_page(**kwargs):
      queried = query.paginate(set_query, **kwargs)
      if mapper is not None:
        queried = query.map_expr(mapper, queried)
      return Page.from_raw(client.query(queried))

    page = get_page(size=page_size)
    yield page

    next_cursor_kind = "after" if page.after is not None else "before"

    next_cursor = getattr(page, next_cursor_kind)
    while next_cursor is not None:
      page = get_page(**{"size": page_size, next_cursor_kind: next_cursor})
      yield page
      next_cursor = getattr(page, next_cursor_kind)

  @staticmethod
  def set_iterator(client, set_query, mapper=None, page_size=None):
    """
    Iterator that keeps getting new values in a set through pagination.

    :param client: A :any:`Client`.
    :param set_query: Set query to paginate, e.g. :any:`match`.
    :param mapper:
      :any:`lambda_expr` for mapping set elements.
    :param page_size:
      Number of instances to be fetched at a time.
    """
    return [
      element
      for page in Page.page_iterator(client, set_query, mapper, page_size)
      for element in page.data]
