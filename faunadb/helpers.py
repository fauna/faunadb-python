"""
Optional functions that may be useful when using FaunaDB.
"""

def page_through_query(query, page_size=100):
  """
  Iterator that keeps getting new pages from a query.

  :param query:
    Function taking paging params (size=_, before=_, after=_)
    and returning a new page ({"data": _, "before": _, "after": _}).
  :param page_size: Number of instances to be fetched at a time.
  :return: Iterator through all elements in "data" of every page.
  """

  page = query(size=page_size)
  for val in page["data"]:
    yield val

  next_cursor = "after" if "after" in page else "before"

  while page[next_cursor] is not None:
    page = query(**{"size": page_size, next_cursor: page[next_cursor]})
    for val in page["data"]:
      yield val
