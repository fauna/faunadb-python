from datetime import date, datetime
import iso8601

from faunadb._json import to_json
from faunadb.objects import Ref, SetRef
from faunadb import query
from tests.helpers import FaunaTestCase

class ObjectsTest(FaunaTestCase):
  def setUp(self):
    super(ObjectsTest, self).setUp()
    self.ref = Ref("classes", "frogs", "123")
    self.json_ref = '{"@ref":"classes/frogs/123"}'

  def test_obj(self):
    self.assertParseJson({"a": 1, "b": 2}, '{"@obj": {"a": 1, "b": 2}}')

  def test_ref(self):
    self.assertJson(self.ref, self.json_ref)

    keys = Ref("keys")
    self.assertEqual(keys.to_class(), keys)
    self.assertRaises(ValueError, keys.id)

    ref = Ref(keys, "123")
    self.assertEqual(ref.to_class(), keys)
    self.assertEqual(ref.id(), "123")

    self.assertRegexCompat(repr(ref), r"Ref\(u?'keys/123'\)")

    self.assertNotEqual(ref, Ref(keys, "456"))

  def test_set(self):
    index = Ref("indexes", "frogs_by_size")
    json_index = '{"@ref":"indexes/frogs_by_size"}'
    match = SetRef(query.match(index, self.ref))
    json_match = '{"@set":{"match":%s,"terms":%s}}' % (json_index, self.json_ref)
    self.assertJson(match, json_match)

    self.assertNotEqual(match, SetRef(query.match(index, Ref("classes", "frogs", "456"))))

  def test_timezone_aware(self):
    # Must be time zone aware.
    self.assertRaises(ValueError, lambda: to_json(datetime.utcnow()))

  def test_time(self):
    test_ts = iso8601.parse_date("1970-01-01T00:00:00.123456Z")
    test_ts_json = '{"@ts":"1970-01-01T00:00:00.123456Z"}'
    self.assertJson(test_ts, test_ts_json)

    self.assertToJson(datetime.fromtimestamp(0, iso8601.UTC), '{"@ts":"1970-01-01T00:00:00Z"}')

  def test_date(self):
    test_date = date(1970, 1, 1)
    test_date_json = '{"@date":"1970-01-01"}'
    self.assertJson(test_date, test_date_json)
