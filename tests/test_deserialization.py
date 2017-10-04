from unittest import TestCase
from iso8601 import parse_date

from faunadb.objects import Ref, SetRef, FaunaTime, Query, Native
from faunadb._json import parse_json

class DeserializationTest(TestCase):

  def test_ref(self):
    self.assertJson('{"@ref":{"id":"classes"}}',
                    Native.CLASSES)

    self.assertJson('{"@ref":{"id":"widgets","class":{"@ref":{"id":"classes"}}}}',
                    Ref("widgets", Native.CLASSES))

    self.assertJson("""{
                      "@ref":{
                        "id":"widgets",
                         "class":{"@ref":{"id":"classes"}},
                         "database":{
                           "@ref":{
                             "id":"db",
                             "class":{"@ref":{"id":"databases"}}
                           }
                         }
                      }
                    }""",
                    Ref("widgets", Native.CLASSES, Ref("db", Native.DATABASES)))

  def test_set_ref(self):
    self.assertJson("""{
                      "@set":{
                        "match":{"@ref":{"id":"widgets","class":{"@ref":{"id":"classes"}}}},
                        "terms":"Laptop"
                      }
                    }""",
                    SetRef({"match": Ref("widgets", Native.CLASSES), "terms": "Laptop"}))

  def test_fauna_time(self):
    self.assertJson('{"@ts":"1970-01-01T00:00:00.123456789Z"}',
                    FaunaTime('1970-01-01T00:00:00.123456789Z'))

  def test_date(self):
    self.assertJson('{"@date":"1970-01-01"}', parse_date("1970-01-01").date())

  def test_bytes(self):
    self.assertJson('{"@bytes":"AQID"}', bytearray(b'\x01\x02\x03'))

  def test_query(self):
    self.assertJson('{"@query": {"lambda": "x", "expr": {"var": "x"}}}',
                    Query({"lambda": "x", "expr": {"var": "x"}}))

  def test_string(self):
    self.assertJson('"a string"', "a string")

  def test_number(self):
    self.assertJson('1', 1)
    self.assertJson('3.14', 3.14)

  def test_empty_array(self):
    self.assertJson('[]', [])

  def test_array(self):
    self.assertJson('[1, "a string"]', [1, "a string"])
    self.assertJson("""[
                      {"@ref":{"id":"widgets","class":{"@ref":{"id":"classes"}}}},
                      {"@date":"1970-01-01"}
                    ]""",
                    [Ref("widgets", Native.CLASSES), parse_date("1970-01-01").date()])

  def test_empty_object(self):
    self.assertJson('{}', {})

  def test_object(self):
    self.assertJson('{"key":"value"}', {"key": "value"})

  def test_object_literal(self):
    self.assertJson('{"@obj":{"@name":"John"}}', {"@name": "John"})

  def test_complex_object(self):
    self.maxDiff = None
    json = """{
      "ref": {"@ref":{"class":{"@ref":{"id":"classes"}},"id":"widget"}},
      "set_ref": {"@set":{"match":{"@ref":{"class":{"@ref":{"id":"classes"}},"id":"widget"}},"terms":"Laptop"}},
      "date": {"@date":"1970-01-01"},
      "time": {"@ts":"1970-01-01T00:00:00.123456789Z"},
      "object": {"@obj":{"key":"value"}},
      "array": [1, 2],
      "string": "a string",
      "number": 1
    }"""

    self.assertJson(json, {
      "ref": Ref("widget", Native.CLASSES),
      "set_ref": SetRef({"match": Ref("widget", Native.CLASSES), "terms": "Laptop"}),
      "date": parse_date("1970-01-01").date(),
      "time": FaunaTime("1970-01-01T00:00:00.123456789Z"),
      "object": {"key": "value"},
      "array": [1, 2],
      "string": "a string",
      "number": 1
    })

  def assertJson(self, json, expected):
    self.assertEqual(parse_json(json), expected)
