from unittest import TestCase

from faunadb.model._util import dict_dup, get_path, set_path, calculate_diff

class ModelUtilTest(TestCase):
  def test_dup(self):
    orig = {"a": 1, "b": 2}
    copy = dict_dup(orig)
    self.assertEqual(copy, orig)
    self.assertIsNot(copy, orig)

  def test_get_path(self):
    self.assertEqual(get_path(["a", "b", "c"], {"a": {"b": {"c": 1}}}), 1)
    self.assertIsNone(get_path(["x", "y", "z"], {"x": {"y": 1}}))

  def test_set_path(self):
    data = {}
    set_path(["a", "b"], 1, data)
    self.assertEqual(data, {"a": {"b": 1}})

  def test_diff(self):
    self.assertEqual(calculate_diff({"a": 1, "b": 2}, {"a": 1, "b": 2}), {})
    self.assertEqual(calculate_diff({"a": 1}, {"a": 2}), {"a": 2})
    self.assertEqual(calculate_diff({"a": 1}, {"a": 1, "b": 2}), {"b": 2})
    self.assertEqual(calculate_diff({"a": 1, "b": 2}, {"a": 1}), {"b": None})
