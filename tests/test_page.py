from faunadb.page import Page
from faunadb.query import create, get, match, select
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
    class_ref = self.client.post("classes", {"name": "gadgets"})["ref"]
    index_ref = self.client.post("indexes", {
      "name": "gadgets_by_n",
      "source": class_ref,
      "path": "data.n",
      "active": True
    })["ref"]

    def create_instance(n):
      q = create(class_ref, {"data": {"n": n}})
      return self.client.query(q)["ref"]

    a = create_instance(0)
    create_instance(1)
    b = create_instance(0)

    gadgets_set = match(index_ref, 0)

    self.assertEqual(list(Page.set_iterator(self.client, gadgets_set, page_size=1)), [a, b])

    query_mapper = lambda a: select(['data', 'n'], get(a))
    query_mapped_iter = Page.set_iterator(self.client, gadgets_set, map_lambda=query_mapper)
    self.assertEqual(list(query_mapped_iter), [0, 0])

    mapped_iter = Page.set_iterator(self.client, gadgets_set, mapper=lambda x: [x])
    self.assertEqual(list(mapped_iter), [[a], [b]])
