def page_through_query(query, page_size=10):
  """
  Iterator that keeps getting new pages from a query.

  :param query:
    Function taking a paging params hash ({"size": _, "before": _, "after": _})
    and returning a new page ({"data": _, "before": _, "after": _}).
  :param page_size: Number of instances to be fetched at a time.
  :return: Iterator through all elements in "data" of every page.
  """

  page = query({"size": page_size})
  for val in page["data"]:
    yield val

  next = "after" if "after" in page else "before"

  while next in page:
    page = query({"size": page_size, next: page[next]})
    for val in page["data"]:
      yield val
