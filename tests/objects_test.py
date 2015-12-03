from datetime import date, datetime
import iso8601

from faunadb.errors import InvalidValue
from faunadb.objects import Event, FaunaTime, Page, Ref, Set
from faunadb._json import parse_json, to_json
from faunadb import query
from test_case import FaunaTestCase

class ObjectsTest(FaunaTestCase):
  def setUp(self):
    super(ObjectsTest, self).setUp()
    self.ref = Ref("classes", "frogs", "123")
    self.json_ref = '{"@ref":"classes/frogs/123"}'

  def test_ref(self):
    assert parse_json(self.json_ref) == self.ref
    assert to_json(self.ref) == self.json_ref

    keys = Ref("keys")
    assert keys.to_class() == keys
    self.assertRaises(InvalidValue, keys.id)

    ref = Ref(keys, "123")
    assert ref.to_class() == keys
    assert ref.id() == "123"

  def test_set(self):
    index = Ref("indexes", "frogs_by_size")
    match = Set(query.match(self.ref, index))
    json_match = '{"@set":{"index":%s,"match":%s}}' % (to_json(index), self.json_ref)
    assert parse_json(json_match) == match
    assert to_json(match) == json_match

  def test_event(self):
    event = Event(123, "create", self.ref)
    event_json = '{"action":"create","resource":{"@ref":"classes/frogs/123"},"ts":123}'
    assert Event.from_raw(parse_json(event_json)) == event
    assert to_json(event) == event_json

    assert to_json(Event(123, None, None)) == '{"ts":123}'

  def test_page(self):
    assert Page.from_raw({"data": 1, "before": 2, "after": 3}) == Page(1, 2, 3)
    assert Page([1, 2, 3], 2, 3).map_data(lambda x: x + 1) == Page([2, 3, 4], 2, 3)

  def test_set_iterator(self):
    class_ref = self.client.post("classes", {"name": "gadgets"})["ref"]
    index_ref = self.client.post("indexes", {
      "name": "gadgets_by_n",
      "source": class_ref,
      "path": "data.n",
      "active": True
    })["ref"]

    def create(n):
      q = query.create(class_ref, query.quote({"data": {"n": n}}))
      return self.client.query(q)["ref"]

    a = create(0)
    create(1)
    b = create(0)

    gadgets_set = query.match(0, index_ref)

    assert list(Page.set_iterator(self.client, gadgets_set, page_size=1)) == [a, b]

    query_mapper = lambda a: query.select(['data', 'n'], query.get(a))
    query_mapped_iter = Page.set_iterator(self.client, gadgets_set, map_lambda=query_mapper)
    assert list(query_mapped_iter) == [0, 0]

    mapped_iter = Page.set_iterator(self.client, gadgets_set, mapper=lambda x: [x])
    assert list(mapped_iter) == [[a], [b]]

  def test_time_conversion(self):
    dt = datetime.now(iso8601.UTC)
    assert FaunaTime(dt).to_datetime() == dt

    dt = datetime.fromtimestamp(0, iso8601.UTC)
    ft = FaunaTime(dt)
    assert ft == FaunaTime("1970-01-01T00:00:00Z")
    assert ft.to_datetime() == dt

  def test_time(self):
    test_ts = FaunaTime("1970-01-01T00:00:00.123456789Z")
    test_ts_json = '{"@ts":"1970-01-01T00:00:00.123456789Z"}'
    assert to_json(test_ts) == test_ts_json
    assert parse_json(test_ts_json) == test_ts

  def test_date(self):
    test_date = date(1970, 1, 1)
    test_date_json = '{"@date":"1970-01-01"}'
    assert to_json(test_date) == test_date_json
    assert parse_json(test_date_json) == test_date
