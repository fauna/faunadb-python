from unittest import TestCase
from iso8601 import parse_date

from faunadb.objects import Ref, SetRef, FaunaTime, Query, Native
from faunadb._json import parse_json

class DeserializationTest(TestCase):

  def test_ref(self):
    self.assertJson('{"@ref":{"id":"collections"}}',
                    Native.COLLECTIONS)

    self.assertJson('{"@ref":{"id":"widgets","collection":{"@ref":{"id":"collections"}}}}',
                    Ref("widgets", Native.COLLECTIONS))

    self.assertJson("""{
                      "@ref":{
                        "id":"widgets",
                         "collection":{"@ref":{"id":"collections"}},
                         "database":{
                           "@ref":{
                             "id":"db",
                             "collection":{"@ref":{"id":"databases"}}
                           }
                         }
                      }
                    }""",
                    Ref("widgets", Native.COLLECTIONS, Ref("db", Native.DATABASES)))

  def test_set_ref(self):
    self.assertJson("""{
                      "@set":{
                        "match":{"@ref":{"id":"widgets","collection":{"@ref":{"id":"collections"}}}},
                        "terms":"Laptop"
                      }
                    }""",
                    SetRef({"match": Ref("widgets", Native.COLLECTIONS), "terms": "Laptop"}))

  def test_fauna_time(self):
    self.assertJson('{"@ts":"1970-01-01T00:00:00.123456789Z"}',
                    FaunaTime('1970-01-01T00:00:00.123456789Z'))

  def test_date(self):
    self.assertJson('{"@date":"1970-01-01"}', parse_date("1970-01-01").date())

  def test_bytes(self):
    self.assertJson('{"@bytes":"AQID"}', bytearray(b'\x01\x02\x03'))

  def test_query(self):
    self.assertJson('{"@query": {"api_version": "3", "lambda": "x", "expr": {"var": "x"}}}',
                    Query({"api_version":"3", "lambda": "x", "expr": {"var": "x"}}))
    self.assertJson('{"@query": {"lambda": "x", "expr": {"var": "x"}}}',
                    Query({"lambda": "x", "expr": {"var": "x"}}))
    self.assertJson('{"@query":  {"lambda": "x", "expr": {"var": "x"}}}',
                    Query({"lambda": "x", "expr": {"var": "x"}}))
    self.assertJson('{"@query": {"api_version": "2.12", "lambda": "x", "expr": {"var": "x"}}}',
                    Query({"api_version": "2.12", "lambda": "x", "expr": {"var": "x"}}))

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
                      {"@ref":{"id":"widgets","collection":{"@ref":{"id":"collections"}}}},
                      {"@date":"1970-01-01"}
                    ]""",
                    [Ref("widgets", Native.COLLECTIONS), parse_date("1970-01-01").date()])

  def test_empty_object(self):
    self.assertJson('{}', {})

  def test_object(self):
    self.assertJson('{"key":"value"}', {"key": "value"})

  def test_object_literal(self):
    self.assertJson('{"@obj":{"@name":"John"}}', {"@name": "John"})

  def test_complex_object(self):
    self.maxDiff = None
    json = """{
      "ref": {"@ref":{"collection":{"@ref":{"id":"collections"}},"id":"widget"}},
      "set_ref": {"@set":{"match":{"@ref":{"collection":{"@ref":{"id":"collections"}},"id":"widget"}},"terms":"Laptop"}},
      "date": {"@date":"1970-01-01"},
      "time": {"@ts":"1970-01-01T00:00:00.123456789Z"},
      "object": {"@obj":{"key":"value"}},
      "array": [1, 2],
      "string": "a string",
      "number": 1
    }"""

    self.assertJson(json, {
      "ref": Ref("widget", Native.COLLECTIONS),
      "set_ref": SetRef({"match": Ref("widget", Native.COLLECTIONS), "terms": "Laptop"}),
      "date": parse_date("1970-01-01").date(),
      "time": FaunaTime("1970-01-01T00:00:00.123456789Z"),
      "object": {"key": "value"},
      "array": [1, 2],
      "string": "a string",
      "number": 1
    })

  def assertJson(self, json, expected):
    self.assertEqual(parse_json(json), expected)
