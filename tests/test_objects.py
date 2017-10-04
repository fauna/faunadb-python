from datetime import date, datetime
import iso8601

from faunadb.objects import FaunaTime, Ref, SetRef, Native
from faunadb import query
from tests.helpers import FaunaTestCase

class ObjectsTest(FaunaTestCase):
  @classmethod
  def setUpClass(cls):
    super(ObjectsTest, cls).setUpClass()
    cls.ref = Ref("123", Ref("frogs", Native.CLASSES))
    cls.json_ref = ('{"@ref":{'
                    '"class":{"@ref":{"class":{"@ref":{"id":"classes"}},"id":"frogs"}},'
                    '"id":"123"'
                    '}}')

  def test_obj(self):
    self.assertParseJson({"a": 1, "b": 2}, '{"@obj": {"a": 1, "b": 2}}')

  def test_ref(self):
    self.assertJson(self.ref, self.json_ref)

    self.assertRaises(ValueError, lambda: Ref(None))

    ref = Ref("123", Native.KEYS)
    self.assertEqual(ref.id(), "123")
    self.assertEqual(ref.class_(), Native.KEYS)
    self.assertEqual(ref.database(), None)

    self.assertRegexCompat(
      repr(ref),
      r"Ref\({u?'id': u?'123', u?'class': Ref\({u?'id': u?'keys'}\)}\)"
    )

  def test_set(self):
    index = Ref("frogs_by_size", Native.INDEXES)
    json_index = '{"@ref":{"class":{"@ref":{"id":"indexes"}},"id":"frogs_by_size"}}'
    match = SetRef(query.match(index, self.ref))
    json_match = '{"@set":{"match":%s,"terms":%s}}' % (json_index, self.json_ref)
    self.assertJson(match, json_match)

    self.assertNotEqual(
      match,
      SetRef(query.match(index, query.ref(query.class_expr("frogs"), "456")))
    )

  def test_time_conversion(self):
    dt = datetime.now(iso8601.UTC)
    self.assertEqual(FaunaTime(dt).to_datetime(), dt)

    # Must be time zone aware.
    self.assertRaises(ValueError, lambda: FaunaTime(datetime.utcnow()))

    dt = datetime.fromtimestamp(0, iso8601.UTC)
    ft = FaunaTime(dt)
    self.assertEqual(ft, FaunaTime("1970-01-01T00:00:00Z"))
    self.assertEqual(ft.to_datetime(), dt)

  def test_time(self):
    test_ts = FaunaTime("1970-01-01T00:00:00.123456789Z")
    test_ts_json = '{"@ts":"1970-01-01T00:00:00.123456789Z"}'
    self.assertJson(test_ts, test_ts_json)

    self.assertToJson(datetime.fromtimestamp(0, iso8601.UTC), '{"@ts":"1970-01-01T00:00:00Z"}')

    self.assertEqual(repr(test_ts), "FaunaTime('1970-01-01T00:00:00.123456789Z')")

    self.assertNotEqual(test_ts, FaunaTime("some_other_time"))

  def test_date(self):
    test_date = date(1970, 1, 1)
    test_date_json = '{"@date":"1970-01-01"}'
    self.assertJson(test_date, test_date_json)
