from __future__ import division
from datetime import date

from faunadb.errors import BadRequest, NotFound
from faunadb.objects import FaunaTime, Ref, SetRef
from faunadb import query
from tests.helpers import FaunaTestCase

class QueryTest(FaunaTestCase):
  def setUp(self):
    super(QueryTest, self).setUp()

    self.class_ref = self.client.query(query.create(Ref("classes"), {"name": "widgets"}))["ref"]

    self.n_index_ref = self.client.query(query.create(Ref("indexes"), {
      "name": "widgets_by_n",
      "source": self.class_ref,
      "terms": [{"field": ["data", "n"]}]
    }))["ref"]

    self.m_index_ref = self.client.query(query.create(Ref("indexes"), {
      "name": "widgets_by_m",
      "source": self.class_ref,
      "terms": [{"field": ["data", "m"]}]
    }))["ref"]

    self.ref_n1 = self._create(n=1)["ref"]
    self.ref_m1 = self._create(m=1)["ref"]
    self.ref_n1m1 = self._create(n=1, m=1)["ref"]

    self.thimble_class_ref = self.client.query(query.create(Ref("classes"), {"name": "thimbles"}))["ref"]

  #region Helpers

  def _set_n(self, n):
    return query.match(self.n_index_ref, n)

  def _set_m(self, m):
    return query.match(self.m_index_ref, m)

  def _create(self, n=0, m=None):
    data = {"n": n} if m is None else {"n": n, "m": m}
    return self._q(query.create(self.class_ref, {"data": data}))

  def _create_thimble(self, data):
    return self._q(query.create(self.thimble_class_ref, {"data": data}))

  def _q(self, query_json):
    return self.client.query(query_json)

  def _set_to_list(self, _set):
    return self._q(query.paginate(_set, size=1000))["data"]

  def _assert_bad_query(self, q):
    self.assertRaises(BadRequest, lambda: self._q(q))

  #endregion

  #region Basic forms

  def test_let_var(self):
    self.assertEqual(self._q(query.let({"x": 1}, query.var("x"))), 1)

  def test_if(self):
    self.assertEqual(self._q(query.if_expr(True, "t", "f")), "t")
    self.assertEqual(self._q(query.if_expr(False, "t", "f")), "f")

  def test_do(self):
    ref = self._create()["ref"]
    self.assertEqual(self._q(query.do(query.delete(ref), 1)), 1)
    self.assertFalse(self._q(query.exists(ref)))


  def test_lambda_query(self):
    self.assertEqual(query.lambda_query(lambda a: query.add(a, a)), {
      "lambda": "a", "expr": {"add": [{"var": "a"}, {"var": "a"}]}
    })

    # pylint: disable=undefined-variable
    expected = query.lambda_query(lambda a: lambda b: lambda c: [a, b, c])
    self.assertEqual(expected, {
      "lambda": "a",
      "expr": {
        "lambda": "b",
        "expr": {
          "lambda": "c",
          "expr": [{"var": "a"}, {"var": "b"}, {"var": "c"}]
        }
      }
    })

  def test_lambda_query_multiple_args(self):
    expected = query.lambda_query(lambda a, b: [b, a])
    self.assertEqual(expected, {
      "lambda": ["a", "b"], "expr": [{"var": "b"}, {"var": "a"}]
    })

  def test_to_lambda(self):
    expr = {"lambda": "a", "expr": {"var": "a"}}
    self.assertEqual(query.lambda_query(lambda a: a), expr)
    self.assertEqual(query.lambda_expr("a", query.var("a")), expr)

  #endregion

  #region Collection functions

  def test_map(self):
    # This is also test_lambda_expr (can't test that alone)
    self.assertEqual(
      self._q(query.map_expr(lambda a: query.multiply(2, a), [1, 2, 3])),
      [2, 4, 6])

    page = query.paginate(self._set_n(1))
    ns = query.map_expr(lambda a: query.select(["data", "n"], query.get(a)), page)
    self.assertEqual(self._q(ns), {"data": [1, 1]})

  def test_foreach(self):
    refs = [self._create()["ref"], self._create()["ref"]]
    self._q(query.foreach(query.delete, refs))
    for ref in refs:
      self.assertFalse(self._q(query.exists(ref)))

  def test_filter(self):
    evens = query.filter_expr(lambda a: query.equals(query.modulo(a, 2), 0), [1, 2, 3, 4])
    self.assertEqual(self._q(evens), [2, 4])

    # Works on page too
    page = query.paginate(self._set_n(1))
    refs_with_m = query.filter_expr(lambda a: query.contains(["data", "m"], query.get(a)), page)
    self.assertEqual(self._q(refs_with_m), {"data": [self.ref_n1m1]})

  def test_take(self):
    self.assertEqual(self._q(query.take(1, [1, 2])), [1])
    self.assertEqual(self._q(query.take(3, [1, 2])), [1, 2])
    self.assertEqual(self._q(query.take(-1, [1, 2])), [])

  def test_drop(self):
    self.assertEqual(self._q(query.drop(1, [1, 2])), [2])
    self.assertEqual(self._q(query.drop(3, [1, 2])), [])
    self.assertEqual(self._q(query.drop(-1, [1, 2])), [1, 2])

  def test_prepend(self):
    self.assertEqual(self._q(query.prepend([1, 2, 3], [4, 5, 6])), [1, 2, 3, 4, 5, 6])

  def test_append(self):
    self.assertEqual(self._q(query.append([4, 5, 6], [1, 2, 3])), [1, 2, 3, 4, 5, 6])

  #endregion

  #region Read functions

  def test_get(self):
    instance = self._create()
    self.assertEqual(self._q(query.get(instance["ref"])), instance)

  def test_paginate(self):
    test_set = self._set_n(1)
    control = [self.ref_n1, self.ref_n1m1]
    self.assertEqual(self._q(query.paginate(test_set)), {"data": control})

    data = []
    page1 = self._q(query.paginate(test_set, size=1))
    data.extend(page1["data"])
    page2 = self._q(query.paginate(test_set, size=1, after=page1["after"]))
    data.extend(page2["data"])
    self.assertEqual(data, control)

    self.assertEqual(self._q(query.paginate(test_set, sources=True)), {
      "data": [
        {"sources": [SetRef(test_set)], "value": self.ref_n1},
        {"sources": [SetRef(test_set)], "value": self.ref_n1m1}
      ]
    })

  def test_exists(self):
    ref = self._create()["ref"]
    self.assertTrue(self._q(query.exists(ref)))
    self._q(query.delete(ref))
    self.assertFalse(self._q(query.exists(ref)))

  def test_count(self):
    self._create(123)
    self._create(123)
    instances = self._set_n(123)
    # `count` is currently only approximate. Should be 2.
    self.assertIsInstance(self._q(query.count(instances)), int)

  #endregion

  #region Write functions

  def test_create(self):
    instance = self._create()
    self.assertIn("ref", instance)
    self.assertIn("ts", instance)
    self.assertEqual(instance["class"], self.class_ref)

  def test_update(self):
    ref = self._create()["ref"]
    got = self._q(query.update(ref, {"data": {"m": 1}}))
    self.assertEqual(got["data"], {"n": 0, "m": 1})

  def test_replace(self):
    ref = self._create()["ref"]
    got = self._q(query.replace(ref, {"data": {"m": 1}}))
    self.assertEqual(got["data"], {"m": 1})

  def test_delete(self):
    ref = self._create()["ref"]
    self._q(query.delete(ref))
    self.assertFalse(self._q(query.exists(ref)))

  def test_insert(self):
    instance = self._create_thimble({"weight": 1})
    ref = instance["ref"]
    ts = instance["ts"]
    prev_ts = ts - 1

    # Add previous event
    inserted = {"data": {"weight": 0}}
    self._q(query.insert(ref, prev_ts, "create", inserted))

    # Get version from previous event
    old = self._q(query.get(ref, ts=prev_ts))
    self.assertEqual(old["data"], {"weight": 0})

  def test_remove(self):
    instance = self._create_thimble({"weight": 0})
    ref = instance["ref"]

    # Change it
    new_instance = self._q(query.replace(ref, {"data": {"weight": 1}}))
    self.assertEqual(self._q(query.get(ref)), new_instance)

    # Delete that event
    self._q(query.remove(ref, new_instance["ts"], "create"))

    # Assert that it was undone
    self.assertEqual(self._q(query.get(ref)), instance)

  #endregion

  #region Sets

  def test_match(self):
    q = self._set_n(1)
    self.assertEqual(self._set_to_list(q), [self.ref_n1, self.ref_n1m1])

  def test_union(self):
    q = query.union(self._set_n(1), self._set_m(1))
    self.assertEqual(self._set_to_list(q), [self.ref_n1, self.ref_m1, self.ref_n1m1])

  def test_intersection(self):
    q = query.intersection(self._set_n(1), self._set_m(1))
    self.assertEqual(self._set_to_list(q), [self.ref_n1m1])

  def test_difference(self):
    q = query.difference(self._set_n(1), self._set_m(1))
    self.assertEqual(self._set_to_list(q), [self.ref_n1]) # but not self.ref_n1m1

  def test_join(self):
    referenced = [self._create(n=12)["ref"], self._create(n=12)["ref"]]
    referencers = [self._create(m=referenced[0])["ref"], self._create(m=referenced[1])["ref"]]

    source = self._set_n(12)
    self.assertEqual(self._set_to_list(source), referenced)

    # For each obj with n=12, get the set of elements whose data.m refers to it.
    joined = query.join(source, lambda a: query.match(self.m_index_ref, a))
    self.assertEqual(self._set_to_list(joined), referencers)

  #endregion

  #region Authentication

  def test_login_logout(self):
    instance_ref = self.client.query(
      query.create(self.class_ref, {"credentials": {"password": "sekrit"}}))["ref"]
    secret = self.client.query(
      query.login(instance_ref, {"password": "sekrit"}))["secret"]
    instance_client = self.get_client(secret=secret)

    self.assertEqual(instance_client.query(
      query.select("ref", query.get(Ref("classes/widgets/self")))), instance_ref)

    self.assertTrue(instance_client.query(query.logout(True)))

  def test_identify(self):
    instance_ref = self.client.query(
      query.create(self.class_ref, {"credentials": {"password": "sekrit"}}))["ref"]
    self.assertTrue(self.client.query(query.identify(instance_ref, "sekrit")))

  #endregion

  #region String functions

  def test_concat(self):
    self.assertEqual(self._q(query.concat(["a", "b", "c"])), "abc")
    self.assertEqual(self._q(query.concat([])), "")
    self.assertEqual(self._q(query.concat(["a", "b", "c"], ".")), "a.b.c")

  def test_casefold(self):
    self.assertEqual(self._q(query.casefold("Hen Wen")), "hen wen")

  #endregion

  #region Time and date functions

  def test_time(self):
    time = "1970-01-01T00:00:00.123456789Z"
    self.assertEqual(self._q(query.time(time)), FaunaTime(time))

    # "now" refers to the current time.
    self.assertIsInstance(self._q(query.time("now")), FaunaTime)

  def test_epoch(self):
    self.assertEqual(self._q(query.epoch(12, "second")), FaunaTime("1970-01-01T00:00:12Z"))
    nano_time = FaunaTime("1970-01-01T00:00:00.123456789Z")
    self.assertEqual(self._q(query.epoch(123456789, "nanosecond")), nano_time)

  def test_date(self):
    self.assertEqual(self._q(query.date("1970-01-01")), date(1970, 1, 1))

  #endregion

  #region Miscellaneous functions

  def test_equals(self):
    self.assertTrue(self._q(query.equals(1, 1, 1)))
    self.assertFalse(self._q(query.equals(1, 1, 2)))
    self.assertTrue(self._q(query.equals(1)))
    self._assert_bad_query(query.equals())

  def test_contains(self):
    obj = {"a": {"b": 1}}
    self.assertTrue(self._q(query.contains(["a", "b"], obj)))
    self.assertTrue(self._q(query.contains("a", obj)))
    self.assertFalse(self._q(query.contains(["a", "c"], obj)))

  def test_select(self):
    obj = {"a": {"b": 1}}
    self.assertEqual(self._q(query.select("a", obj)), {"b": 1})
    self.assertEqual(self._q(query.select(["a", "b"], obj)), 1)
    self.assertIsNone(self._q(query.select_with_default("c", obj, None)))
    self.assertRaises(NotFound, lambda: self._q(query.select("c", obj)))

  def test_select_array(self):
    arr = [1, 2, 3]
    self.assertEqual(self._q(query.select(2, arr)), 3)
    self.assertRaises(NotFound, lambda: self._q(query.select(3, arr)))

  def test_add(self):
    self.assertEqual(self._q(query.add(2, 3, 5)), 10)
    self._assert_bad_query(query.add())

  def test_multiply(self):
    self.assertEqual(self._q(query.multiply(2, 3, 5)), 30)
    self._assert_bad_query(query.multiply())

  def test_subtract(self):
    self.assertEqual(self._q(query.subtract(2, 3, 5)), -6)
    self.assertEqual(self._q(query.subtract(2)), 2)
    self._assert_bad_query(query.subtract())

  def test_divide(self):
    self.assertEqual(self._q(query.divide(2.0, 3, 5)), 2 / 15)
    self.assertEqual(self._q(query.divide(2)), 2)
    self._assert_bad_query(query.divide(1, 0))
    self._assert_bad_query(query.divide())

  def test_modulo(self):
    self.assertEqual(self._q(query.modulo(5, 2)), 1)
    # This is (15 % 10) % 2
    self.assertEqual(self._q(query.modulo(15, 10, 2)), 1)
    self.assertEqual(self._q(query.modulo(2)), 2)
    self._assert_bad_query(query.modulo(1, 0))
    self._assert_bad_query(query.modulo())

  def test_lt(self):
    self.assertTrue(self._q(query.lt(1, 2)))

  def test_lte(self):
    self.assertTrue(self._q(query.lte(1, 1)))

  def test_gt(self):
    self.assertTrue(self._q(query.gt(2, 1)))

  def test_gte(self):
    self.assertTrue(self._q(query.gte(1, 1)))

  def test_and(self):
    self.assertFalse(self._q(query.and_expr(True, True, False)))
    self.assertTrue(self._q(query.and_expr(True, True, True)))
    self.assertTrue(self._q(query.and_expr(True)))
    self.assertFalse(self._q(query.and_expr(False)))
    self._assert_bad_query(query.and_expr())

  def test_or(self):
    self.assertTrue(self._q(query.or_expr(False, False, True)))
    self.assertFalse(self._q(query.or_expr(False, False, False)))
    self.assertTrue(self._q(query.or_expr(True)))
    self.assertFalse(self._q(query.or_expr(False)))
    self._assert_bad_query(query.or_expr())

  def test_not(self):
    self.assertFalse(self._q(query.not_expr(True)))
    self.assertTrue(self._q(query.not_expr(False)))

  #endregion

  #region Helpers tests

  def test_object(self):
    self.assertEqual(self._q({"x": query.let({"x": 1}, query.var("x"))}), {"x": 1})

  def test_varargs(self):
    # Works for lists too
    self.assertEqual(self._q(query.add([2, 3, 5])), 10)
    # Works for a variable equal to a list
    self.assertEqual(self._q(query.let({"x": [2, 3, 5]}, query.add(query.var("x")))), 10)

  #endregion
