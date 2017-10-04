from faunadb.page import Page
from faunadb import query
from tests.helpers import FaunaTestCase

class PageTest(FaunaTestCase):
  def test_page(self):
    self.assertEqual(
      Page.from_raw({"data": 1, "before": 2, "after": 3}),
      Page(1, 2, 3))
    self.assertEqual(
      Page([1, 2, 3], 2, 3).map_data(lambda x: x + 1),
      Page([2, 3, 4], 2, 3))

  def test_set_iterator(self):
    class_ref = self.client.query(query.create_class({"name": "gadgets"}))["ref"]
    index_ref = self.client.query(query.create_index({
      "name": "gadgets_by_n",
      "source": class_ref,
      "terms": [{"field": ["data", "n"]}]
    }))["ref"]

    def create(n):
      q = query.create(class_ref, {"data": {"n": n}})
      return self.client.query(q)["ref"]

    a = create(0)
    create(1)
    b = create(0)

    gadgets_set = query.match(index_ref, 0)

    self.assertEqual(list(Page.set_iterator(self.client, gadgets_set, page_size=1)), [a, b])

    query_mapper = lambda a: query.select(['data', 'n'], query.get(a))
    query_mapped_iter = Page.set_iterator(self.client, gadgets_set, map_lambda=query_mapper)
    self.assertEqual(list(query_mapped_iter), [0, 0])

    mapped_iter = Page.set_iterator(self.client, gadgets_set, mapper=lambda x: [x])
    self.assertEqual(list(mapped_iter), [[a], [b]])

  def test_repr(self):
    self.assertEqual(
      repr(Page([1, 2, 3], ["before"])),
      "Page(data=[1, 2, 3], before=['before'], after=None)")
