from faunadb.errors import BadRequest, NotFound
from faunadb.objects import Set
from faunadb import query
from test_case import FaunaTestCase

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

  def _set_n(self, n):
    return query.match(n, self.n_index_ref)

  def _set_m(self, m):
    return query.match(m, self.m_index_ref)

  def _create(self, n=0, m=None):
    data = query.object(n=n) if m is None else query.object(n=n, m=m)
    return self._q(query.create(self.class_ref, query.object(data=data)))

  def _q(self, query_json):
    return self.client.query(query_json)

  def _set_to_list(self, _set):
    return self._q(query.paginate(_set, size=1000))["data"]

  def _assert_bad_query(self, q):
    self.assertRaises(BadRequest, lambda: self._q(q))

  def test_let_var(self):
    assert self._q(query.let({"x": 1}, query.var("x"))) == 1

  def test_if(self):
    assert self._q(query.if_expr(True, "t", "f")) == "t"
    assert self._q(query.if_expr(False, "t", "f")) == "f"

  def test_do(self):
    widget = self._create()
    assert self._q(query.do([query.delete(widget["ref"]), 1])) == 1
    assert self._q(query.exists(widget["ref"])) == False

  def test_object(self):
    # unlike quote, contents are evaluated
    assert self._q(query.object(x=query.let({"x": 1}, query.var("x")))) == {"x": 1}

  def test_quote(self):
    quoted = query.let({"x": 1}, query.var("x"))
    assert self._q(query.quote(quoted)) == quoted

  def test_map(self):
    # This is also test_lambda_expr (can't test that alone)
    double = query.lambda_expr("x", query.multiply([2, query.var("x")]))
    assert self._q(query.map(double, [1, 2, 3])) == [2, 4, 6]

    get_n = query.lambda_expr("x", query.select(["data", "n"], query.get(query.var("x"))))
    page = query.paginate(self._set_n(1))
    ns = query.map(get_n, page)
    assert self._q(ns)["data"] == [1, 1]

  def test_foreach(self):
    refs = [self._create()["ref"], self._create()["ref"]]
    q = query.foreach(query.lambda_expr("x", query.delete(query.var("x"))), refs)
    self._q(q)
    for ref in refs:
      assert self._q(query.exists(ref)) == False

  def test_get(self):
    widget = self._create()
    assert self._q(query.get(widget["ref"])) == widget

  def test_paginate(self):
    test_set = self._set_n(1)
    assert self._q(query.paginate(test_set)) == {"data": [self.ref_n1, self.ref_n1m1]}
    assert self._q(query.paginate(test_set, size=1)) ==\
      {"data": [self.ref_n1], "after": self.ref_n1m1}
    assert self._q(query.paginate(test_set, sources=True)) == {
      "data": [
        {"sources": [Set(test_set)], "value": self.ref_n1},
        {"sources": [Set(test_set)], "value": self.ref_n1m1}
      ]
    }

  def test_exists(self):
    ref = self._create()["ref"]
    assert self._q(query.exists(ref)) == True
    self._q(query.delete(ref))
    assert self._q(query.exists(ref)) == False

  def test_count(self):
    self._create(123)
    self._create(123)
    widgets = self._set_n(123)
    # `count` is currently only approximate. Should be 2.
    assert isinstance(self._q(query.count(widgets)), int)

  def test_create(self):
    widget = self._create()
    assert "ref" in widget
    assert "ts" in widget
    assert widget["class"] == self.class_ref

  def test_update(self):
    ref = self._create()["ref"]
    got = self._q(query.update(ref, query.object(data=query.object(m=1))))
    assert got["data"] == {"n": 0, "m": 1}

  def test_replace(self):
    ref = self._create()["ref"]
    got = self._q(query.replace(ref, query.object(data=query.object(m=1))))
    assert got["data"] == {"m": 1}

  def test_delete(self):
    ref = self._create()["ref"]
    self._q(query.delete(ref))
    assert self._q(query.exists(ref)) == False

  def test_match(self):
    q = self._set_n(1)
    assert self._set_to_list(q) == [self.ref_n1, self.ref_n1m1]

  def test_union(self):
    q = query.union(self._set_n(1), self._set_m(1))
    assert self._set_to_list(q) == [self.ref_n1, self.ref_m1, self.ref_n1m1]

  def test_intersection(self):
    q = query.intersection(self._set_n(1), self._set_m(1))
    assert self._set_to_list(q) == [self.ref_n1m1]

  def test_difference(self):
    q = query.difference(self._set_n(1), self._set_m(1))
    assert self._set_to_list(q) == [self.ref_n1] # but not self.ref_n1m1

  def test_join(self):
    referenced = [self._create(n=12)["ref"], self._create(n=12)["ref"]]
    referencers = [self._create(m=referenced[0])["ref"], self._create(m=referenced[1])["ref"]]

    source = self._set_n(12)
    assert self._set_to_list(source) == referenced

    # For each obj with n=12, get the set of elements whose data.m refers to it.
    joined = query.join(
      source,
      query.lambda_expr(
        "x",
        query.match(query.var("x"), self.m_index_ref)))
    assert self._set_to_list(joined) == referencers

  def test_equals(self):
    assert self._q(query.equals([1, 1, 1])) == True
    assert self._q(query.equals([1, 1, 2])) == False
    assert self._q(query.equals([1])) == True
    self._assert_bad_query(query.equals([]))

  def test_concat(self):
    assert self._q(query.concat(["a", "b", "c"])) == "abc"
    assert self._q(query.concat([])) == ""

  def test_contains(self):
    obj = query.quote({"a": {"b": 1}})
    assert self._q(query.contains(["a", "b"], obj)) == True
    assert self._q(query.contains("a", obj)) == True
    assert self._q(query.contains(["a", "c"], obj)) == False

  def test_select(self):
    obj = query.quote({"a": {"b": 1}})
    assert self._q(query.select("a", obj)) == {"b": 1}
    assert self._q(query.select(["a", "b"], obj)) == 1
    assert self._q(query.select_with_default("c", obj, None)) == None
    self.assertRaises(NotFound, lambda: self._q(query.select("c", obj)))

  def test_select_array(self):
    arr = [1, 2, 3]
    assert self._q(query.select(2, arr)) == 3
    self.assertRaises(NotFound, lambda: self._q(query.select(3, arr)))

  def test_add(self):
    assert self._q(query.add([2, 3, 5])) == 10
    self._assert_bad_query(query.add([]))

  def test_multiply(self):
    assert self._q(query.multiply([2, 3, 5])) == 30
    self._assert_bad_query(query.multiply([]))

  def test_subtract(self):
    assert self._q(query.subtract([2, 3, 5])) == -6
    assert self._q(query.subtract([2])) == 2
    self._assert_bad_query(query.subtract([]))

  def test_divide(self):
    assert self._q(query.divide([2, 3, 5])) == 2/15
    assert self._q(query.divide([2])) == 2
    self._assert_bad_query(query.divide([1, 0]))
    self._assert_bad_query(query.divide([]))
