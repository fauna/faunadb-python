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
    self.assertJson(SetRef({"match": Ref("indexes/widgets"), "terms": "Laptop"}),
                    '{"@set":{"match":{"@ref":"indexes/widgets"},"terms":"Laptop"}}')

  def test_fauna_time(self):
    self.assertJson(FaunaTime('1970-01-01T00:00:00.123456789Z'),
                    '{"@ts":"1970-01-01T00:00:00.123456789Z"}')
    self.assertJson(datetime.fromtimestamp(0, iso8601.UTC),
                    '{"@ts":"1970-01-01T00:00:00Z"}')

  #region Basic forms

  def test_let(self):
    self.assertJson(query.let({"x": 1}, 1), '{"in":1,"let":{"x":1}}')

  def test_vars(self):
    self.assertJson(query.var("x"), '{"var":"x"}')

  def test_if_expr(self):
    self.assertJson(query.if_expr(True, "true", "false"),
                    '{"else":"false","if":true,"then":"true"}')

  def test_do(self):
    self.assertJson(query.do(query.add(1, 2), query.var("x")),
                    '{"do":[{"add":[1,2]},{"var":"x"}]}')

  def test_lambda_query(self):
    #pylint: disable=unnecessary-lambda
    self.assertJson(query.lambda_query(lambda a: a), '{"expr":{"var":"a"},"lambda":"a"}')
    self.assertJson(query.lambda_query(lambda a, b: query.add(a, b)),
                    '{"expr":{"add":[{"var":"a"},{"var":"b"}]},"lambda":["a","b"]}')

  def test_lambda_expr(self):
    self.assertJson(query.lambda_expr("a", query.var("a")), '{"expr":{"var":"a"},"lambda":"a"}')
    self.assertJson(query.lambda_expr(["a", "b"], query.add(query.var("a"), query.var("b"))),
                    '{"expr":{"add":[{"var":"a"},{"var":"b"}]},"lambda":["a","b"]}')

  #endregion

  #region Collection functions

  def test_map_expr(self):
    self.assertJson(query.map_expr(lambda a: a, [1, 2, 3]),
                    '{"collection":[1,2,3],"map":{"expr":{"var":"a"},"lambda":"a"}}')

  def test_foreach(self):
    self.assertJson(query.foreach(lambda a: a, [1, 2, 3]),
                    '{"collection":[1,2,3],"foreach":{"expr":{"var":"a"},"lambda":"a"}}')

  def test_filter_expr(self):
    self.assertJson(query.filter_expr(lambda a: a, [True, False, True]),
                    '{"collection":[true,false,true],"filter":{"expr":{"var":"a"},"lambda":"a"}}')

  def test_take(self):
    self.assertJson(query.take(2, [1, 2, 3]), '{"collection":[1,2,3],"take":2}')

  def test_drop(self):
    self.assertJson(query.drop(2, [1, 2, 3]), '{"collection":[1,2,3],"drop":2}')

  def test_prepend(self):
    self.assertJson(query.prepend([1, 2], [3, 4]), '{"collection":[3,4],"prepend":[1,2]}')

  def test_append(self):
    self.assertJson(query.append([1, 2], [3, 4]), '{"append":[1,2],"collection":[3,4]}')

  #endregion

  #region Read functions

  def test_get(self):
    self.assertJson(query.get(Ref("classes/widget")), '{"get":{"@ref":"classes/widget"}}')
    self.assertJson(query.get(Ref("classes/widget"), ts=123),
                    '{"get":{"@ref":"classes/widget"},"ts":123}')

  def test_paginate(self):
    self.assertJson(query.paginate(Ref("classes/widget")), '{"paginate":{"@ref":"classes/widget"}}')
    self.assertJson(query.paginate(Ref("classes/widget"),
                                   size=1,
                                   ts=123,
                                   after=Ref("classes/widget/1"),
                                   before=Ref("classes/widget/10"),
                                   events=True,
                                   sources=True),
                    ('{"after":{"@ref":"classes/widget/1"},'
                     '"before":{"@ref":"classes/widget/10"},'
                     '"events":true,"paginate":{"@ref":"classes/widget"},'
                     '"size":1,"sources":true,"ts":123}'))

  def test_exists(self):
    self.assertJson(query.exists(Ref("classes/widget")), '{"exists":{"@ref":"classes/widget"}}')
    self.assertJson(query.exists(Ref("classes/widget"), ts=123),
                    '{"exists":{"@ref":"classes/widget"},"ts":123}')

  def test_count(self):
    self.assertJson(query.count(Ref("classes/widget")), '{"count":{"@ref":"classes/widget"}}')
    self.assertJson(query.count(Ref("classes/widget"), events=True),
                    '{"count":{"@ref":"classes/widget"},"events":true}')

  #endregion

  #region Write functions

  def test_create(self):
    json = ('{"create":{"@ref":"classes/widget"},'
            '"params":{"object":{"data":{"object":{"name":"Laptop"}}}}}')
    self.assertJson(query.create(Ref("classes/widget"), {
      "data": {"name": "Laptop"}
    }), json)

  def test_update(self):
    json = ('{"params":{"object":{"data":{"object":{"name":"Laptop"}}}},'
            '"update":{"@ref":"classes/widget"}}')
    self.assertJson(query.update(Ref("classes/widget"), {
      "data": {"name": "Laptop"}
    }), json)

  def test_replace(self):
    json = ('{"params":{"object":{"data":{"object":{"name":"Laptop"}}}},'
            '"replace":{"@ref":"classes/widget"}}')
    self.assertJson(query.replace(Ref("classes/widget"), {
      "data": {"name": "Laptop"}
    }), json)

  def test_delete(self):
    self.assertJson(query.delete(Ref("classes/widget")), '{"delete":{"@ref":"classes/widget"}}')

  def test_insert(self):
    json = ('{"action":"create","insert":{"@ref":"classes/widget"},'
            '"params":{"object":{"data":{"object":{"name":"Laptop"}}}},"ts":123}')
    self.assertJson(query.insert(Ref("classes/widget"), ts=123, action="create", params={
      "data": {"name": "Laptop"}
    }), json)

  def test_remove(self):
    self.assertJson(query.remove(Ref("classes/widget"), ts=123, action="create"),
                    '{"action":"create","remove":{"@ref":"classes/widget"},"ts":123}')

  def test_create_class(self):
    self.assertJson(query.create_class({"name": "widget"}),
                    '{"create_class":{"object":{"name":"widget"}}}')

  def test_create_database(self):
    self.assertJson(query.create_database({"name": "db-name"}),
                    '{"create_database":{"object":{"name":"db-name"}}}')

  def test_create_index(self):
    self.assertJson(query.create_index({"name": "index-name", "source": Ref("classes/widget")}),
                    ('{"create_index":{"object":{"name":"index-name",'
                     '"source":{"@ref":"classes/widget"}}}}'))

  def test_create_key(self):
    self.assertJson(query.create_key({"database": Ref("databases/db-name"), "role": "client"}),
                    ('{"create_key":{"object":{"database":{"@ref":"databases/db-name"},'
                     '"role":"client"}}}'))

  #endregion

  #region Sets

  def test_match(self):
    self.assertJson(query.match(Ref("indexes/widget")), '{"match":{"@ref":"indexes/widget"}}')
    self.assertJson(query.match(Ref("indexes/widget"), "Laptop"),
                    '{"match":{"@ref":"indexes/widget"},"terms":"Laptop"}')

  def test_union(self):
    self.assertJson(query.union(), '{"union":[]}')
    self.assertJson(query.union(Ref("indexes/widget")), '{"union":{"@ref":"indexes/widget"}}')
    self.assertJson(query.union(Ref("indexes/widget"), Ref("indexes/things")),
                    '{"union":[{"@ref":"indexes/widget"},{"@ref":"indexes/things"}]}')

  def test_intersection(self):
    self.assertJson(query.intersection(), '{"intersection":[]}')
    self.assertJson(query.intersection(Ref("indexes/widget")),
                    '{"intersection":{"@ref":"indexes/widget"}}')
    self.assertJson(query.intersection(Ref("indexes/widget"), Ref("indexes/things")),
                    '{"intersection":[{"@ref":"indexes/widget"},{"@ref":"indexes/things"}]}')

  def test_difference(self):
    self.assertJson(query.difference(), '{"difference":[]}')
    self.assertJson(query.difference(Ref("indexes/widget")),
                    '{"difference":{"@ref":"indexes/widget"}}')
    self.assertJson(query.difference(Ref("indexes/widget"), Ref("indexes/things")),
                    '{"difference":[{"@ref":"indexes/widget"},{"@ref":"indexes/things"}]}')

  def test_distinct(self):
    self.assertJson(query.distinct(SetRef({"match": Ref("indexes/widget")})),
                    '{"distinct":{"@set":{"match":{"@ref":"indexes/widget"}}}}')

  def test_join(self):
    self.assertJson(query.join(query.match(Ref("indexes/widget")), Ref("indexes/things")),
                    '{"join":{"match":{"@ref":"indexes/widget"}},"with":{"@ref":"indexes/things"}}')

  #endregion

  #region Authentication

  def test_login(self):
    json = '{"login":{"@ref":"classes/widget/1"},"params":{"object":{"password":"abracadabra"}}}'
    self.assertJson(query.login(Ref("classes/widget/1"), {"password": "abracadabra"}), json)

  def test_logout(self):
    self.assertJson(query.logout(True), '{"logout":true}')

  def test_identify(self):
    self.assertJson(query.identify(Ref("classes/widget/1"), "abracadabra"),
                    '{"identify":{"@ref":"classes/widget/1"},"password":"abracadabra"}')

  #endregion

  #region String functions

  def test_concat(self):
    self.assertJson(query.concat(["a", "b"]), '{"concat":["a","b"]}')
    self.assertJson(query.concat(["a", "b"], "/"), '{"concat":["a","b"],"separator":"/"}')

  def test_casefold(self):
    self.assertJson(query.casefold("a string"), '{"casefold":"a string"}')

  #endregion

  #region Time and date functions

  def test_time(self):
    self.assertJson(query.time("1970-01-01T00:00:00+00:00"), '{"time":"1970-01-01T00:00:00+00:00"}')

  def test_epoch(self):
    self.assertJson(query.epoch(1, "second"), '{"epoch":1,"unit":"second"}')
    self.assertJson(query.epoch(1, "milisecond"), '{"epoch":1,"unit":"milisecond"}')
    self.assertJson(query.epoch(1, "microsecond"), '{"epoch":1,"unit":"microsecond"}')
    self.assertJson(query.epoch(1, "nanosecond"), '{"epoch":1,"unit":"nanosecond"}')

  def test_date(self):
    self.assertJson(query.date("1970-01-01"), '{"date":"1970-01-01"}')

  #endregion

  #region Miscellaneous functions

  def test_next_id(self):
    self.assertJson(query.next_id(), '{"next_id":null}')

  def test_equals(self):
    self.assertJson(query.equals(1), '{"equals":1}')
    self.assertJson(query.equals(1, 2), '{"equals":[1,2]}')
    self.assertJson(query.equals([1, 2]), '{"equals":[1,2]}')

  def test_contains(self):
    json = ('{"contains":["favorites","foods"],'
            '"in":{"object":{"favorites":{"object":{"foods":["steak"]}}}}}')
    self.assertJson(query.contains(["favorites", "foods"],
                                   {"favorites": {"foods": ["steak"]}}), json)

  def test_select(self):
    json = ('{"from":{"object":{"favorites":{"object":{"foods":["steak"]}}}},'
            '"select":["favorites","foods",0]}')
    self.assertJson(query.select(["favorites", "foods", 0],
                                 {"favorites": {"foods": ["steak"]}}), json)

  def test_select_with_default(self):
    json = ('{"default":"no food","from":{"object":{"favorites":{"object":{"foods":["steak"]}}}},'
            '"select":["favorites","foods",0]}')
    self.assertJson(query.select_with_default(["favorites", "foods", 0],
                                              {"favorites": {"foods": ["steak"]}}, "no food"), json)

  def test_add(self):
    self.assertJson(query.add(1), '{"add":1}')
    self.assertJson(query.add(1, 2, 3), '{"add":[1,2,3]}')
    self.assertJson(query.add([1, 2, 3]), '{"add":[1,2,3]}')

  def test_multiply(self):
    self.assertJson(query.multiply(1), '{"multiply":1}')
    self.assertJson(query.multiply(1, 2, 3), '{"multiply":[1,2,3]}')
    self.assertJson(query.multiply([1, 2, 3]), '{"multiply":[1,2,3]}')

  def test_subtract(self):
    self.assertJson(query.subtract(1), '{"subtract":1}')
    self.assertJson(query.subtract(1, 2, 3), '{"subtract":[1,2,3]}')
    self.assertJson(query.subtract([1, 2, 3]), '{"subtract":[1,2,3]}')

  def test_divide(self):
    self.assertJson(query.divide(1), '{"divide":1}')
    self.assertJson(query.divide(1, 2, 3), '{"divide":[1,2,3]}')
    self.assertJson(query.divide([1, 2, 3]), '{"divide":[1,2,3]}')

  def test_modulo(self):
    self.assertJson(query.modulo(1), '{"modulo":1}')
    self.assertJson(query.modulo(1, 2, 3), '{"modulo":[1,2,3]}')
    self.assertJson(query.modulo([1, 2, 3]), '{"modulo":[1,2,3]}')

  def test_lt(self):
    self.assertJson(query.lt(1), '{"lt":1}')
    self.assertJson(query.lt(1, 2, 3), '{"lt":[1,2,3]}')
    self.assertJson(query.lt([1, 2, 3]), '{"lt":[1,2,3]}')

  def test_lte(self):
    self.assertJson(query.lte(1), '{"lte":1}')
    self.assertJson(query.lte(1, 2, 3), '{"lte":[1,2,3]}')
    self.assertJson(query.lte([1, 2, 3]), '{"lte":[1,2,3]}')

  def test_gt(self):
    self.assertJson(query.gt(1), '{"gt":1}')
    self.assertJson(query.gt(1, 2, 3), '{"gt":[1,2,3]}')
    self.assertJson(query.gt([1, 2, 3]), '{"gt":[1,2,3]}')

  def test_gte(self):
    self.assertJson(query.gte(1), '{"gte":1}')
    self.assertJson(query.gte(1, 2, 3), '{"gte":[1,2,3]}')
    self.assertJson(query.gte([1, 2, 3]), '{"gte":[1,2,3]}')

  def test_and_expr(self):
    self.assertJson(query.and_expr(True), '{"and":true}')
    self.assertJson(query.and_expr(True, False, False), '{"and":[true,false,false]}')
    self.assertJson(query.and_expr([True, False, False]), '{"and":[true,false,false]}')

  def test_or_expr(self):
    self.assertJson(query.or_expr(False), '{"or":false}')
    self.assertJson(query.or_expr(False, True, True), '{"or":[false,true,true]}')
    self.assertJson(query.or_expr([False, True, True]), '{"or":[false,true,true]}')

  def test_not_expr(self):
    self.assertJson(query.not_expr(False), '{"not":false}')

  #endregion

  def assertJson(self, obj, expected):
    self.assertEqual(to_json(obj, sort_keys=True), expected)
