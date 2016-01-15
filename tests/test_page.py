from faunadb.page import Page
from faunadb import query
from tests.helpers import FaunaTestCase

class PageTest(FaunaTestCase):
  def setUp(self):
    super(PageTest, self).setUp()

    self.class_ref = self.client.post("classes", {"name": "gadgets"})["ref"]
    index_ref = self.client.post("indexes", {
      "name": "gadgets_by_n",
      "source": self.class_ref,
      "path": "data.n",
      "active": True
    })["ref"]

    self.a = self.create(0)
    self.create(1)
    self.b = self.create(0)

    self.gadgets_set = query.match(index_ref, 0)

  def create(self, n):
    q = query.create(self.class_ref, query.quote({"data": {"n": n}}))
    return self.client.query(q)["ref"]

  def test_from_raw(self):
    self.assertEqual(
      Page.from_raw({"data": 1, "before": 2, "after": 3}),
      Page(1, 2, 3))

  def test_map_data(self):
    self.assertEqual(
      Page([1, 2, 3], 2, 3).map_data(lambda x: x + 1),
      Page([2, 3, 4], 2, 3))

  def test_page_iterator(self):
    iterator = Page.page_iterator(self.client, self.gadgets_set, page_size=1)
    self.assertEqual([page.data for page in iterator], [[self.a], [self.b]])

  def test_set_iterator(self):
    iterator = Page.set_iterator(self.client, self.gadgets_set, page_size=1)
    self.assertEqual(list(iterator), [self.a, self.b])

  def test_mapper(self):
    def mapper(a):
      return query.select(['data', 'n'], query.get(a))
    iterator = Page.set_iterator(self.client, self.gadgets_set, mapper=mapper)
    self.assertEqual(list(iterator), [0, 0])
