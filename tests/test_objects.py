from datetime import date, datetime
import iso8601

from faunadb.objects import FaunaTime, Ref, SetRef
from faunadb import query
from tests.helpers import FaunaTestCase

class ObjectsTest(FaunaTestCase):
  def setUp(self):
    super(ObjectsTest, self).setUp()
    self.ref = Ref("classes", "frogs", "123")
    self.json_ref = '{"@ref":"classes/frogs/123"}'

  def test_ref(self):
    self.assertJson(self.ref, self.json_ref)

    keys = Ref("keys")
    self.assertEqual(keys.to_class, keys)
    self.assertRaises(ValueError, keys.id)

    ref = Ref(keys, "123")
    self.assertEqual(ref.to_class, keys)
    self.assertEqual(ref.id, "123")

  def test_set(self):
    index = Ref("indexes", "frogs_by_size")
    json_index = '{"@ref":"indexes/frogs_by_size"}'
    match = SetRef(query.match(index, self.ref))
    json_match = '{"@set":{"match":%s,"terms":%s}}' % (json_index, self.json_ref)
    self.assertJson(match, json_match)

  def test_time_conversion(self):
    dt = datetime.now(iso8601.UTC)
    self.assertEqual(FaunaTime(dt).to_datetime(), dt)

    dt = datetime.fromtimestamp(0, iso8601.UTC)
    ft = FaunaTime(dt)
    self.assertEqual(ft, FaunaTime("1970-01-01T00:00:00Z"))
    self.assertEqual(ft.to_datetime(), dt)

  def test_time(self):
    test_ts = FaunaTime("1970-01-01T00:00:00.123456789Z")
    test_ts_json = '{"@ts":"1970-01-01T00:00:00.123456789Z"}'
    self.assertJson(test_ts, test_ts_json)

  def test_date(self):
    test_date = date(1970, 1, 1)
    test_date_json = '{"@date":"1970-01-01"}'
    self.assertJson(test_date, test_date_json)
