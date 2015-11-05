from faunadb.model._util import dict_dup, get_path, set_path, calculate_diff

from unittest import TestCase

class ModelUtilTest(TestCase):
  def test_dup(self):
    orig = {"a": 1, "b": 2}
    copy = dict_dup(orig)
    assert copy == orig
    assert copy is not orig

  def test_get_path(self):
    assert get_path(["a", "b", "c"], {"a": {"b": {"c": 1}}}) == 1
    assert get_path(["x", "y", "z"], {"x": {"y": 1}}) == None

  def test_set_path(self):
    data = {}
    set_path(["a", "b"], 1, data)
    assert data == {"a": {"b": 1}}

  def test_diff(self):
    assert calculate_diff({"a": 1, "b": 2}, {"a": 1, "b": 2}) == {}
    assert calculate_diff({"a": 1}, {"a": 2}) == {"a": 2}
    assert calculate_diff({"a": 1}, {"a": 1, "b": 2}) == {"b": 2}
    assert calculate_diff({"a": 1, "b": 2}, {"a": 1}) == {"b": None}
