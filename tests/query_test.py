from random import randint

from faunadb.errors import BadRequest, NotFound
from faunadb.objects import Ref, Set
from faunadb import query
from test_case import FaunaTestCase

def _randint():
  return randint(0, 1000000)

class QueryTest(FaunaTestCase):
  def setUp(self):
    super(QueryTest, self).setUp()

    # Set up sample model
    self.client.post("classes", {"name": "widgets"})
    # index by n
    self.client.post("indexes", {
      "name": "widgets_by_n",
      "source": Ref("classes", "widgets"),
      "path": "data.n"
    })
    self.n_index_ref = Ref("indexes", "widgets_by_n")

    self.client.post("indexes", {
      "name": "widgets_by_m",
      "source": Ref("classes", "widgets"),
      "path": "data.m"

    })
    self.m_index_ref = Ref("indexes", "widgets_by_m")

    self.ref_n1 = self._create(n=1)["ref"]
    self.ref_m1 = self._create(m=1)["ref"]
    self.ref_n1m1 = self._create(n=1, m=1)["ref"]


  def _set_n(self, n):
    return Set.match(n, self.n_index_ref)
  def _set_m(self, m):
    return Set.match(m, self.m_index_ref)

  def _create(self, n=0, m=None):
    data = query.object(n=n) if m is None else query.object(n=n, m=m)
    return self._q(query.create(Ref("classes", "widgets"), query.object(data=data)))

  def _q(self, query_json):
    return self.client.query(query_json).resource

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
    assert self._q(query.object(x=1, y=2)) == {"x": 1, "y": 2}

  def test_quote(self):
    quoted = query.let({"x": 1}, query.var("x"))
    assert self._q(query.quote(quoted)) == quoted

  # Can't test lambda_expr alone, but test it with map.
  def test_map(self):
    double = query.lambda_expr("x", query.multiply([2, query.var("x")]))
    assert self._q(query.map(double, [1, 2, 3])) == [2, 4, 6]

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
    _set = self._set_n(1)
    assert self._q(query.paginate(_set)) == {"data": [self.ref_n1, self.ref_n1m1]}
    assert self._q(query.paginate(_set, size=1)) == {"data": [self.ref_n1], "after": self.ref_n1m1}
    assert self._q(query.paginate(_set, sources=True)) == {
      "data": [
        {"sources": [_set], "value": self.ref_n1},
        {"sources": [_set], "value": self.ref_n1m1}
      ]
    }

  def test_exists(self):
    ref = self._create()["ref"]
    assert self._q(query.exists(ref)) == True
    self._q(query.delete(ref))
    assert self._q(query.exists(ref)) == False

  def test_count(self):
    n = _randint()
    self._create(n)
    self._create(n)
    widgets = self._set_n(n)
    # `count` is currently only approximate. Should be 2.
    assert isinstance(self._q(query.count(widgets)), int)

  def test_create(self):
    widget = self._create()
    assert "ref" in widget
    assert "ts" in widget
    assert widget["class"] == Ref("classes", "widgets")

  def test_update(self):
    ref = self._create()["ref"]
    got = self._q(query.update(ref, query.object(data=query.object(n=1))))
    assert got["data"] == {"n": 1}

  def test_replace(self):
    ref = self._create()["ref"]
    got = self._q(query.replace(ref, query.object(data=query.object(m=1))))
    assert got["data"] == {"m": 1}

  def test_delete(self):
    ref = self._create()["ref"]
    self._q(query.delete(ref))
    assert self._q(query.exists(ref)) == False

  def test_union(self):
    q = Set.union([self._set_n(1), self._set_m(1)])
    assert self._set_to_list(q) == [self.ref_n1, self.ref_m1, self.ref_n1m1]

  def test_intersection(self):
    q = Set.intersection([self._set_n(1), self._set_m(1)])
    assert self._set_to_list(q) == [self.ref_n1m1]

  def test_difference(self):
    q = Set.difference(self._set_n(1), [self._set_m(1)])
    assert self._set_to_list(q) == [self.ref_n1] # but not self.ref_n1m1

  # TODO: `core` issue #1950
  # The lambda has an error in it, but an error is not thrown. Instead we just get an empty list.
  def test_error_in_join_lambda(self):
    self.client.post("classes", {"name": "foos"})
    self.client.post("indexes", {
      "name": "foos_by_n",
      "source": Ref("classes", "foos"),
      "path": "data.n"
    })
    index_ref = Ref("indexes", "foos_by_n")

    self.client.post("indexes", {
      "name": "foos_by_m",
      "source": Ref("classes", "foos"),
      "path": "data.m"
    })
    other_index_ref = Ref("indexes", "foos_by_m")

    self._q(query.create(Ref("classes", "foos"), query.object(data=query.object(n=1))))
    source = Set.match(1, index_ref)
    print "source set:", self._q(source)
    print "source set contents:", self._set_to_list(source)
    target = query.lambda_expr(
      "x",
      Set.match(query.divide([1, 0]), other_index_ref))
      # Set.match(query.select("not selectable", query.var("x")), index_ref))

    print "join set:", self._q(Set.join(source, target))

    from logging import getLogger
    self.client.logger = getLogger(__name__)
    print "join set contents:", self._set_to_list(Set.join(source, target))

  '''
  TODO: Must fix test_error_in_join_lambda first
  def test_join(self):
    # source_set is a normal set.
    # target takes an element in source_set and returns a set.
    # applies target to each element in source_set and merges the resulting sets.

    # For each element x with x.n=1, get the set of elements with y.m = x.m

    n = _randint()
    m1 = _randint()
    m2 = _randint()
    self._create(n=n, m=m1)
    self._create(n=n, m=m2)
    r1 = self._create(n=100, m=m1)
    r2 = self._create(n=101, m=m2)

    source = self._set_n(n)
    target = query.lambda_expr("x", Set.match(query.select(query.var("x"), "m"), self.m_index_ref))
    q = Set.join(source, target)

    #assert self._q(q) == [r1, r2]
  '''

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
    assert self._q(query.select("c", obj, default=None)) == None
    self.assertRaises(NotFound, lambda: self._q(query.select("c", obj)))

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
