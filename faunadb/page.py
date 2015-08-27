class Page(object):
  """
  A single pagination result.
  See :samp:`paginate` in the `docs <https://faunadb.com/documentation#queries-read_functions>`__.
  """

  @staticmethod
  def from_json(json):
    return Page(json["data"], json.get("before"), json.get("after"))

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

  def map_data(self, fun):
    return Page([fun(x) for x in self.data], self.before, self.after)

  def __repr__(self):
    return "Page(data=%s, before=%s, after=%s)" % (self.data, self.before, self.after)

  @staticmethod
  def page_through_query(query, page_size=16):
    """
    Iterator that keeps getting new pages from a pagination query.

    :param query:
      Function taking paging params :samp:`query(size=_, before=_, after=_)`
      and returning a new :any:`Page`.

      At least one of :samp:`before` or :samp:`after` will be :samp:None.
    :param page_size:
      Number of instances to be fetched at a time.
      Passed straight through to :samp:`query`.
    :return:
      Iterator through all elements in every page.
    """

    page = query(size=page_size)
    for val in page.data:
      yield val

    next_cursor = "after" if page.after is not None else "before"

    while getattr(page, next_cursor) is not None:
      page = query(**{"size": page_size, next_cursor: getattr(page, next_cursor)})
      for val in page.data:
        yield val
