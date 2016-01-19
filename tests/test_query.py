from __future__ import division
from datetime import date as dt_date
from threading import Thread
from time import sleep

from faunadb.errors import BadRequest, NotFound
from faunadb.objects import FaunaTime, Ref, Set
from faunadb.query import *
from tests.helpers import FaunaTestCase

class QueryTest(FaunaTestCase):
  def setUp(self):
    super(QueryTest, self).setUp()

    self.class_ref = self.client.post("classes", {"name": "widgets"})["ref"]

    self.n_index_ref = self.client.post("indexes", {
      "name": "widgets_by_n",
      "source": self.class_ref,
      "path": "data.n",
      "active": True
    })["ref"]

    self.m_index_ref = self.client.post("indexes", {
      "name": "widgets_by_m",
      "source": self.class_ref,
      "path": "data.m",
      "active": True
    })["ref"]

    self.ref_n1 = self._create(n=1)["ref"]
    self.ref_m1 = self._create(m=1)["ref"]
    self.ref_n1m1 = self._create(n=1, m=1)["ref"]

    self.thimble_class_ref = self.client.post("classes", {"name": "thimbles"})["ref"]

  #region Helpers

  def _set_n(self, n):
    return match(self.n_index_ref, n)

  def _set_m(self, m):
    return match(self.m_index_ref, m)

  def _create(self, n=0, m=None):
    data = {"n": n} if m is None else {"n": n, "m": m}
    return self._q(create(self.class_ref, {"data": data}))

  def _create_thimble(self, data):
    return self._q(create(self.thimble_class_ref, {"data": data}))

  def _q(self, query_json):
    return self.client.query(query_json)

  def _set_to_list(self, _set):
    return self._q(paginate(_set, size=1000))["data"]

  def _assert_bad_query(self, q):
    self.assertRaises(BadRequest, lambda: self._q(q))

  #endregion

  #region Basic forms

  def test_let_var(self):
    assert self._q(let({"x": 1}, var("x"))) == 1

  def test_if(self):
    assert self._q(if_expr(True, "t", "f")) == "t"
    assert self._q(if_expr(False, "t", "f")) == "f"

  def test_do(self):
    ref = self._create()["ref"]
    assert self._q(do(delete(ref), 1)) == 1
    assert self._q(exists(ref)) is False

  def test_lambda_query(self):
    assert to_query(lambda a: add(a, a)) == {
      "lambda": "auto0", "expr": {"add": [{"var": "auto0"}, {"var": "auto0"}]}
    }

    # pylint: disable=undefined-variable
    expected = to_query(lambda a: lambda b: lambda c: [a, b, c])
    assert expected == {
      "lambda": "auto0",
      "expr": {
        "lambda": "auto1",
        "expr": {
          "lambda": "auto2",
          "expr": [{"var": "auto0"}, {"var": "auto1"}, {"var": "auto2"}]
        }
      }
    }

    # Error in lambda should not affect future queries.
    with self.assertRaises(Exception):
      def fail():
        raise Exception("foo")
      to_query(lambda a: fail())
    assert to_query(lambda a: a) == {"lambda": "auto0", "expr": {"var": "auto0"}}

  def test_lambda_query_multiple_args(self):
    expected = to_query(lambda a, b: [b, a])
    assert expected == {
      "lambda": ["auto0", "auto1"],
      "expr": [{"var": "auto1"}, {"var": "auto0"}]
    }

  def test_lambda_query_multithreaded(self):
    """Test that lambda_query works in simultaneous threads."""
    events = []

    def do_a():
      def do_lambda(a):
        events.append(0)
        sleep(1)
        events.append(2)
        return a
      self.assertEqual(
        to_query(do_lambda),
        {"lambda": "auto0", "expr": {"var": "auto0"}})

    def do_b():
      # This happens while thread 'a' has incremented its auto name to auto1,
      # but that doesn't affect thread 'b'.
      self.assertEqual(
        to_query(lambda a: a),
        {"lambda": "auto0", "expr": {"var": "auto0"}})
      events.append(1)

    t = Thread(name="a", target=do_a)
    t2 = Thread(name="b", target=do_b)
    t.start()
    t2.start()
    t.join()
    t2.join()

    # Assert that events happened in the order expected.
    self.assertEqual(events, [0, 1, 2])

  #endregion

  #region Collection functions

  def test_map(self):
    # This is also test_lambda_expr (can't test that alone)
    self.assertEqual(
      self._q(map_expr(lambda a: multiply(2, a), [1, 2, 3])),
      [2, 4, 6])

    page = paginate(self._set_n(1))
    ns = map_expr(lambda a: select(["data", "n"], get(a)), page)
    self.assertEqual(self._q(ns), {"data": [1, 1]})

  def test_foreach(self):
    refs = [self._create()["ref"], self._create()["ref"]]
    self._q(foreach(delete, refs))
    for ref in refs:
      self.assertFalse(self._q(exists(ref)))

  def test_filter(self):
    evens = filter_expr(lambda a: equals(modulo(a, 2), 0), [1, 2, 3, 4])
    self.assertEqual(self._q(evens), [2, 4])

    # Works on page too
    page = paginate(self._set_n(1))
    refs_with_m = filter_expr(lambda a: contains(["data", "m"], get(a)), page)
    self.assertEqual(self._q(refs_with_m), {"data": [self.ref_n1m1]})

  def test_take(self):
    self.assertEqual(self._q(take(1, [1, 2])), [1])
    self.assertEqual(self._q(take(3, [1, 2])), [1, 2])
    self.assertEqual(self._q(take(-1, [1, 2])), [])

  def test_drop(self):
    self.assertEqual(self._q(drop(1, [1, 2])), [2])
    self.assertEqual(self._q(drop(3, [1, 2])), [])
    self.assertEqual(self._q(drop(-1, [1, 2])), [1, 2])

  def test_prepend(self):
    self.assertEqual(self._q(prepend([1, 2, 3], [4, 5, 6])), [1, 2, 3, 4, 5, 6])

  def test_append(self):
    self.assertEqual(self._q(append([4, 5, 6], [1, 2, 3])), [1, 2, 3, 4, 5, 6])

  #endregion

  #region Read functions

  def test_get(self):
    instance = self._create()
    self.assertEqual(self._q(get(instance["ref"])), instance)

  def test_paginate(self):
    test_set = self._set_n(1)
    control = [self.ref_n1, self.ref_n1m1]
    self.assertEqual(self._q(paginate(test_set)), {"data": control})

    data = []
    page1 = self._q(paginate(test_set, size=1))
    data.extend(page1["data"])
    page2 = self._q(paginate(test_set, size=1, after=page1["after"]))
    data.extend(page2["data"])
    self.assertEqual(data, control)

    self.assertEqual(self._q(paginate(test_set, sources=True)), {
      "data": [
        {"sources": [Set(test_set)], "value": self.ref_n1},
        {"sources": [Set(test_set)], "value": self.ref_n1m1}
      ]
    })

  def test_exists(self):
    ref = self._create()["ref"]
    self.assertTrue(self._q(exists(ref)))
    self._q(delete(ref))
    self.assertFalse(self._q(exists(ref)))

  def test_count(self):
    self._create(123)
    self._create(123)
    instances = self._set_n(123)
    # `count` is currently only approximate. Should be 2.
    self.assertIsInstance(self._q(count(instances)), int)

  #endregion

  #region Write functions

  def test_create(self):
    instance = self._create()
    self.assertIn("ref", instance)
    self.assertIn("ts", instance)
    self.assertEqual(instance["class"], self.class_ref)

  def test_update(self):
    ref = self._create()["ref"]
    got = self._q(update(ref, {"data": {"m": 1}}))
    self.assertEqual(got["data"], {"n": 0, "m": 1})

  def test_replace(self):
    ref = self._create()["ref"]
    got = self._q(replace(ref, {"data": {"m": 1}}))
    self.assertEqual(got["data"], {"m": 1})

  def test_delete(self):
    ref = self._create()["ref"]
    self._q(delete(ref))
    self.assertFalse(self._q(exists(ref)))

  #endregion

  #region Sets

  def test_insert(self):
    instance = self._create_thimble({"weight": 1})
    ref = instance["ref"]
    ts = instance["ts"]
    prev_ts = ts - 1

    # Add previous event
    inserted = {"data": {"weight": 0}}
    self._q(insert(ref, prev_ts, "create", inserted))

    # Get version from previous event
    old = self._q(get(ref, ts=prev_ts))
    self.assertEqual(old["data"], {"weight": 0})

  def test_remove(self):
    instance = self._create_thimble({"weight": 0})
    ref = instance["ref"]

    # Change it
    new_instance = self._q(replace(ref, {"data": {"weight": 1}}))
    self.assertEqual(self._q(get(ref)), new_instance)

    # Delete that event
    self._q(remove(ref, new_instance["ts"], "create"))

    # Assert that it was undone
    self.assertEqual(self._q(get(ref)), instance)

  def test_match(self):
    q = self._set_n(1)
    self.assertEqual(self._set_to_list(q), [self.ref_n1, self.ref_n1m1])

  def test_union(self):
    q = union(self._set_n(1), self._set_m(1))
    self.assertEqual(self._set_to_list(q), [self.ref_n1, self.ref_m1, self.ref_n1m1])

  def test_intersection(self):
    q = intersection(self._set_n(1), self._set_m(1))
    self.assertEqual(self._set_to_list(q), [self.ref_n1m1])

  def test_difference(self):
    q = difference(self._set_n(1), self._set_m(1))
    self.assertEqual(self._set_to_list(q), [self.ref_n1]) # but not self.ref_n1m1

  def test_join(self):
    referenced = [self._create(n=12)["ref"], self._create(n=12)["ref"]]
    referencers = [self._create(m=referenced[0])["ref"], self._create(m=referenced[1])["ref"]]

    source = self._set_n(12)
    self.assertEqual(self._set_to_list(source), referenced)

    # For each obj with n=12, get the set of elements whose data.m refers to it.
    joined = join(source, lambda a: match(self.m_index_ref, a))
    self.assertEqual(self._set_to_list(joined), referencers)

  #endregion

  #region Authentication

  def test_login_logout(self):
    instance_ref = self.client.query(
      create(self.class_ref, {"credentials": {"password": "sekrit"}}))["ref"]
    secret = self.client.query(
      login(instance_ref, {"password": "sekrit"}))["secret"]
    instance_client = self.get_client(secret=secret)

    self.assertEqual(instance_client.query(
      select("ref", get(Ref("classes/widgets/self")))), instance_ref)

    self.assertTrue(instance_client.query(logout(True)))

  def test_identify(self):
    instance_ref = self.client.query(
      create(self.class_ref, {"credentials": {"password": "sekrit"}}))["ref"]
    self.assertTrue(self.client.query(identify(instance_ref, "sekrit")))

  #endregion

  #region String functions

  def test_concat(self):
    self.assertEqual(self._q(concat(["a", "b", "c"])), "abc")
    self.assertEqual(self._q(concat([])), "")
    self.assertEqual(self._q(concat(["a", "b", "c"], ".")), "a.b.c")

  def test_casefold(self):
    self.assertEqual(self._q(casefold("Hen Wen")), "hen wen")

  #endregion

  #region Time and date functions

  def test_time(self):
    time_str = "1970-01-01T00:00:00.123456789Z"
    self.assertEqual(self._q(time(time_str)), FaunaTime(time_str))

    # "now" refers to the current time.
    self.assertIsInstance(self._q(time("now")), FaunaTime)

  def test_epoch(self):
    self.assertEqual(self._q(epoch(12, "second")), FaunaTime("1970-01-01T00:00:12Z"))
    nano_time = FaunaTime("1970-01-01T00:00:00.123456789Z")
    self.assertEqual(self._q(epoch(123456789, "nanosecond")), nano_time)

  def test_date(self):
    self.assertEqual(self._q(date("1970-01-01")), dt_date(1970, 1, 1))

  #endregion

  #region Miscellaneous functions

  def test_equals(self):
    self.assertTrue(self._q(equals(1, 1, 1)))
    self.assertFalse(self._q(equals(1, 1, 2)))
    self.assertTrue(self._q(equals(1)))
    self._assert_bad_query(equals())

  def test_contains(self):
    obj = {"a": {"b": 1}}
    self.assertTrue(self._q(contains(["a", "b"], obj)))
    self.assertTrue(self._q(contains("a", obj)))
    self.assertFalse(self._q(contains(["a", "c"], obj)))

  def test_select(self):
    obj = {"a": {"b": 1}}
    self.assertEqual(self._q(select("a", obj)), {"b": 1})
    self.assertEqual(self._q(select(["a", "b"], obj)), 1)
    self.assertIsNone(self._q(select_with_default("c", obj, None)))
    self.assertRaises(NotFound, lambda: self._q(select("c", obj)))

  def test_select_array(self):
    arr = [1, 2, 3]
    self.assertEqual(self._q(select(2, arr)), 3)
    self.assertRaises(NotFound, lambda: self._q(select(3, arr)))

  def test_add(self):
    self.assertEqual(self._q(add(2, 3, 5)), 10)
    self._assert_bad_query(add())

  def test_multiply(self):
    self.assertEqual(self._q(multiply(2, 3, 5)), 30)
    self._assert_bad_query(multiply())

  def test_subtract(self):
    self.assertEqual(self._q(subtract(2, 3, 5)), -6)
    self.assertEqual(self._q(subtract(2)), 2)
    self._assert_bad_query(subtract())

  def test_divide(self):
    self.assertEqual(self._q(divide(2.0, 3, 5)), 2 / 15)
    self.assertEqual(self._q(divide(2)), 2)
    self._assert_bad_query(divide(1, 0))
    self._assert_bad_query(divide())

  def test_modulo(self):
    self.assertEqual(self._q(modulo(5, 2)), 1)
    # This is (15 % 10) % 2
    self.assertEqual(self._q(modulo(15, 10, 2)), 1)
    self.assertEqual(self._q(modulo(2)), 2)
    self._assert_bad_query(modulo(1, 0))
    self._assert_bad_query(modulo())

  def test_lt(self):
    self.assertTrue(self._q(lt(1, 2)))

  def test_lte(self):
    self.assertTrue(self._q(lte(1, 1)))

  def test_gt(self):
    self.assertTrue(self._q(gt(2, 1)))

  def test_gte(self):
    self.assertTrue(self._q(gte(1, 1)))

  def test_and(self):
    self.assertFalse(self._q(and_expr(True, True, False)))
    assert self._q(and_expr(True, True, True)) is True
    assert self._q(and_expr(True)) is True
    self.assertFalse(self._q(and_expr(False)))
    self._assert_bad_query(and_expr())

  def test_or(self):
    self.assertTrue(self._q(or_expr(False, False, True)))
    self.assertFalse(self._q(or_expr(False, False, False)))
    self.assertTrue(self._q(or_expr(True)))
    self.assertFalse(self._q(or_expr(False)))
    self._assert_bad_query(or_expr())

  def test_not(self):
    self.assertFalse(self._q(not_expr(True)))
    self.assertTrue(self._q(not_expr(False)))

  #endregion

  #region Helpers tests

  def test_object(self):
    assert self._q({"x": let({"x": 1}, var("x"))}) == {"x": 1}

  def test_varargs(self):
    # Works for lists too
    self.assertEqual(self._q(add([2, 3, 5])), 10)
    # Works for a variable equal to a list
    self.assertEqual(self._q(let({"x": [2, 3, 5]}, add(var("x")))), 10)

  #endregion
