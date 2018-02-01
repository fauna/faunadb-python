import sys
from datetime import datetime
from unittest import TestCase
import iso8601

from faunadb import query
from faunadb.objects import Ref, SetRef, FaunaTime, Query, Native
from faunadb._json import to_json

class SerializationTest(TestCase):

  def test_native(self):
    self.assertJson(Native.CLASSES, '{"@ref":{"id":"classes"}}')
    self.assertJson(Native.INDEXES, '{"@ref":{"id":"indexes"}}')
    self.assertJson(Native.DATABASES, '{"@ref":{"id":"databases"}}')
    self.assertJson(Native.FUNCTIONS, '{"@ref":{"id":"functions"}}')
    self.assertJson(Native.KEYS, '{"@ref":{"id":"keys"}}')

  def test_ref(self):
    self.assertJson(Ref("classes"),
                    '{"@ref":{"id":"classes"}}')
    self.assertJson(Ref("widgets", Native.CLASSES),
                    '{"@ref":{"class":{"@ref":{"id":"classes"}},"id":"widgets"}}')

  def test_set_ref(self):
    self.assertJson(SetRef({"match": Ref("widgets", Native.INDEXES), "terms": "Laptop"}),
                    ('{'
                     '"@set":{'
                     '"match":{"@ref":{"class":{"@ref":{"id":"indexes"}},"id":"widgets"}},'
                     '"terms":"Laptop"'
                     '}'
                     '}'))

  def test_fauna_time(self):
    self.assertJson(FaunaTime('1970-01-01T00:00:00.123456789Z'),
                    '{"@ts":"1970-01-01T00:00:00.123456789Z"}')
    self.assertJson(datetime.fromtimestamp(0, iso8601.UTC),
                    '{"@ts":"1970-01-01T00:00:00Z"}')

  def test_bytes(self):
    self.assertJson(bytearray(b'\x01\x02\x03'), '{"@bytes":"AQID"}')
    if sys.version_info.major == 3:
      # In Python 3.x we should also accept bytes
      self.assertJson(b'\x01\x02\x03', '{"@bytes":"AQID"}')

  def test_query(self):
    self.assertJson(Query({"lambda": "x", "expr": {"var": "x"}}),
                    '{"@query":{"expr":{"var":"x"},"lambda":"x"}}')

  #region Basic forms

  def test_abort(self):
    self.assertJson(
      query.abort("aborting"),
      '{"abort":"aborting"}'
    )

  def test_at(self):
    self.assertJson(
      query.at(datetime.fromtimestamp(0, iso8601.UTC), query.get(query.index("widgets"))),
      '{"at":{"@ts":"1970-01-01T00:00:00Z"},"expr":{"get":{"index":"widgets"}}}'
    )

  def test_let(self):
    self.assertJson(query.let({"x": 1}, 1), '{"in":1,"let":{"x":1}}')

  def test_vars(self):
    self.assertJson(query.var("x"), '{"var":"x"}')

  def test_if_expr(self):
    self.assertJson(query.if_(True, "true", "false"),
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
    self.assertJson(query.lambda_("a", query.var("a")), '{"expr":{"var":"a"},"lambda":"a"}')
    self.assertJson(query.lambda_(["a", "b"], query.add(query.var("a"), query.var("b"))),
                    '{"expr":{"add":[{"var":"a"},{"var":"b"}]},"lambda":["a","b"]}')

  #endregion

  #region Collection functions

  def test_map_expr(self):
    self.assertJson(query.map_(lambda a: a, [1, 2, 3]),
                    '{"collection":[1,2,3],"map":{"expr":{"var":"a"},"lambda":"a"}}')

  def test_foreach(self):
    self.assertJson(query.foreach(lambda a: a, [1, 2, 3]),
                    '{"collection":[1,2,3],"foreach":{"expr":{"var":"a"},"lambda":"a"}}')

  def test_filter_expr(self):
    self.assertJson(query.filter_(lambda a: a, [True, False, True]),
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
    self.assertJson(query.get(query.class_("widget")), '{"get":{"class":"widget"}}')
    self.assertJson(query.get(query.class_("widget"), ts=123),
                    '{"get":{"class":"widget"},"ts":123}')

  def test_paginate(self):
    self.assertJson(query.paginate(query.class_("widget")), '{"paginate":{"class":"widget"}}')
    self.assertJson(query.paginate(query.class_("widget"),
                                   size=1,
                                   ts=123,
                                   after=query.ref(query.class_("widget"), "1"),
                                   before=query.ref(query.class_("widget"), "10"),
                                   events=True,
                                   sources=True),
                    ('{"after":{"id":"1","ref":{"class":"widget"}},'
                     '"before":{"id":"10","ref":{"class":"widget"}},'
                     '"events":true,"paginate":{"class":"widget"},'
                     '"size":1,"sources":true,"ts":123}'))

  def test_exists(self):
    self.assertJson(query.exists(query.class_("widget")), '{"exists":{"class":"widget"}}')
    self.assertJson(query.exists(query.class_("widget"), ts=123),
                    '{"exists":{"class":"widget"},"ts":123}')

  #endregion

  #region Write functions

  def test_create(self):
    json = ('{"create":{"class":"widget"},'
            '"params":{"object":{"data":{"object":{"name":"Laptop"}}}}}')
    self.assertJson(query.create(query.class_("widget"), {
      "data": {"name": "Laptop"}
    }), json)

  def test_update(self):
    json = ('{"params":{"object":{"data":{"object":{"name":"Laptop"}}}},'
            '"update":{"class":"widget"}}')
    self.assertJson(query.update(query.class_("widget"), {
      "data": {"name": "Laptop"}
    }), json)

  def test_replace(self):
    json = ('{"params":{"object":{"data":{"object":{"name":"Laptop"}}}},'
            '"replace":{"class":"widget"}}')
    self.assertJson(query.replace(query.class_("widget"), {
      "data": {"name": "Laptop"}
    }), json)

  def test_delete(self):
    self.assertJson(query.delete(query.class_("widget")), '{"delete":{"class":"widget"}}')

  def test_insert(self):
    json = ('{"action":"create","insert":{"class":"widget"},'
            '"params":{"object":{"data":{"object":{"name":"Laptop"}}}},"ts":123}')
    self.assertJson(query.insert(query.class_("widget"), ts=123, action="create", params={
      "data": {"name": "Laptop"}
    }), json)

  def test_remove(self):
    self.assertJson(query.remove(query.class_("widget"), ts=123, action="create"),
                    '{"action":"create","remove":{"class":"widget"},"ts":123}')

  def test_create_class(self):
    self.assertJson(query.create_class({"name": "widget"}),
                    '{"create_class":{"object":{"name":"widget"}}}')

  def test_create_database(self):
    self.assertJson(query.create_database({"name": "db-name"}),
                    '{"create_database":{"object":{"name":"db-name"}}}')

  def test_create_index(self):
    self.assertJson(
      query.create_index({"name": "index-name", "source": query.class_("widget")}),
      '{"create_index":{"object":{"name":"index-name","source":{"class":"widget"}}}}'
    )

  def test_create_key(self):
    self.assertJson(
      query.create_key({"database": query.database("db-name"), "role": "client"}),
      '{"create_key":{"object":{"database":{"database":"db-name"},"role":"client"}}}'
    )

  #endregion

  #region Sets

  def test_match(self):
    self.assertJson(query.match(query.index("widget")), '{"match":{"index":"widget"}}')
    self.assertJson(query.match(query.index("widget"), "Laptop"),
                    '{"match":{"index":"widget"},"terms":"Laptop"}')

  def test_union(self):
    self.assertJson(query.union(), '{"union":[]}')
    self.assertJson(query.union(query.index("widget")), '{"union":{"index":"widget"}}')
    self.assertJson(query.union(query.index("widget"), query.index("things")),
                    '{"union":[{"index":"widget"},{"index":"things"}]}')

  def test_intersection(self):
    self.assertJson(query.intersection(), '{"intersection":[]}')
    self.assertJson(query.intersection(query.index("widget")),
                    '{"intersection":{"index":"widget"}}')
    self.assertJson(query.intersection(query.index("widget"), query.index("things")),
                    '{"intersection":[{"index":"widget"},{"index":"things"}]}')

  def test_difference(self):
    self.assertJson(query.difference(), '{"difference":[]}')
    self.assertJson(query.difference(query.index("widget")),
                    '{"difference":{"index":"widget"}}')
    self.assertJson(query.difference(query.index("widget"), query.index("things")),
                    '{"difference":[{"index":"widget"},{"index":"things"}]}')

  def test_distinct(self):
    self.assertJson(query.distinct(SetRef({"match": query.index("widget")})),
                    '{"distinct":{"@set":{"match":{"index":"widget"}}}}')

  def test_join(self):
    self.assertJson(query.join(query.match(query.index("widget")), query.index("things")),
                    '{"join":{"match":{"index":"widget"}},"with":{"index":"things"}}')

  #endregion

  #region Authentication

  def test_login(self):
    self.assertJson(
      query.login(query.ref(query.class_("widget"), "1"), {"password": "abracadabra"}),
      '{"login":{"id":"1","ref":{"class":"widget"}},"params":{"object":{"password":"abracadabra"}}}'
    )

  def test_logout(self):
    self.assertJson(query.logout(True), '{"logout":true}')

  def test_identify(self):
    self.assertJson(query.identify(query.ref(query.class_("widget"), "1"), "abracadabra"),
                    '{"identify":{"id":"1","ref":{"class":"widget"}},"password":"abracadabra"}')

  def test_identity(self):
    self.assertJson(query.identity(), '{"identity":null}')

  def test_has_identity(self):
    self.assertJson(query.has_identity(), '{"has_identity":null}')

  #endregion

  #region String functions

  def test_concat(self):
    self.assertJson(query.concat(["a", "b"]), '{"concat":["a","b"]}')
    self.assertJson(query.concat(["a", "b"], "/"), '{"concat":["a","b"],"separator":"/"}')

  def test_casefold(self):
    self.assertJson(query.casefold("a string"), '{"casefold":"a string"}')
    self.assertJson(query.casefold("a string", "NFD"), '{"casefold":"a string","normalizer":"NFD"}')

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

  def test_new_id(self):
    self.assertJson(query.new_id(), '{"new_id":null}')

  def test_database(self):
    self.assertJson(query.database("db-name"), '{"database":"db-name"}')

  def test_index(self):
    self.assertJson(query.index("index-name"), '{"index":"index-name"}')

  def test_class(self):
    self.assertJson(query.class_("class-name"), '{"class":"class-name"}')

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
    self.assertJson(query.and_(True), '{"and":true}')
    self.assertJson(query.and_(True, False, False), '{"and":[true,false,false]}')
    self.assertJson(query.and_([True, False, False]), '{"and":[true,false,false]}')

  def test_or_expr(self):
    self.assertJson(query.or_(False), '{"or":false}')
    self.assertJson(query.or_(False, True, True), '{"or":[false,true,true]}')
    self.assertJson(query.or_([False, True, True]), '{"or":[false,true,true]}')

  def test_not_expr(self):
    self.assertJson(query.not_(False), '{"not":false}')

  #endregion

  def assertJson(self, obj, expected):
    self.assertEqual(to_json(obj, sort_keys=True), expected)
