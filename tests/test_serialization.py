from unittest import TestCase
from datetime import datetime
import iso8601

from faunadb import query
from faunadb.objects import Ref, SetRef, FaunaTime
from faunadb._json import to_json

class SerializationTest(TestCase):

  def test_ref(self):
    self.assertJson(Ref("classes"), '{"@ref":"classes"}')
    self.assertJson(Ref("classes", "widgets"), '{"@ref":"classes/widgets"}')

  def test_set_ref(self):
    self.assertJson(SetRef({"match": Ref("indexes/widgets"), "terms": "Laptop"}), '{"@set":{"match":{"@ref":"indexes/widgets"},"terms":"Laptop"}}');

  def test_fauna_time(self):
    self.assertJson(FaunaTime('1970-01-01T00:00:00.123456789Z'), '{"@ts":"1970-01-01T00:00:00.123456789Z"}')
    self.assertJson(datetime.fromtimestamp(0, iso8601.UTC), '{"@ts":"1970-01-01T00:00:00Z"}')

  #region Basic forms

  def test_let(self):
    self.assertJson(query.let({"x": 1}, 1), '{"in":1,"let":{"x":1}}')

  def test_vars(self):
    self.assertJson(query.var("x"), '{"var":"x"}')

  def test_if_expr(self):
    self.assertJson(query.if_expr(True, "true", "false"), '{"else":"false","if":true,"then":"true"}')

  def test_do(self):
    self.assertJson(query.do(query.add(1,2), query.var("x")), '{"do":[{"add":[1,2]},{"var":"x"}]}');

  def test_lambda_query(self):
    self.assertJson(query.lambda_query(lambda a: a), '{"expr":{"var":"a"},"lambda":"a"}')
    self.assertJson(query.lambda_query(lambda a, b: query.add(a, b)),
                    '{"expr":{"add":[{"var":"a"},{"var":"b"}]},"lambda":["a","b"]}')

  def test_lambda_expr(self):
    self.assertJson(query.lambda_expr("a", query.var("a")), '{"expr":{"var":"a"},"lambda":"a"}')
    self.assertJson(query.lambda_expr(["a", "b"], query.add(query.var("a"), query.var("b"))),
                    '{"expr":{"add":[{"var":"a"},{"var":"b"}]},"lambda":["a","b"]}')

  #endregion

  def assertJson(self, obj, expected):
    self.assertEqual(to_json(obj, sort_keys=True), expected)
