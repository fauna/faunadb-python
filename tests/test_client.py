from faunadb.client import Client
from faunadb.errors import NotFound
from tests.helpers import FaunaTestCase

class ClientTest(FaunaTestCase):
  def test_parse_secret(self):
    self.assertEqual(Client._parse_secret(("user", "pass")), ("user", "pass"))
    self.assertEqual(Client._parse_secret("user"), ("user", ""))
    self.assertEqual(Client._parse_secret("user:pass"), ("user", "pass"))
    self.assertRaises(ValueError, lambda: Client._parse_secret(("user", "pass", "potato")))

  def test_ping(self):
    self.assertEqual(self.client.ping("all"), "Scope all is OK")

  def test_get(self):
    self.assertIsInstance(self.client.get("classes")["data"], list)

  def _create_class(self):
    return self.client.post("classes", {"name": "my_class"})

  def _create_instance(self):
    return self.client.post("classes/my_class", {})

  def test_post(self):
    cls = self._create_class()
    self.assertEqual(self.client.get(cls["ref"]), cls)

  def test_put(self):
    self._create_class()
    instance = self._create_instance()
    instance = self.client.put(instance["ref"], {"data": {"a": 2}})

    self.assertEqual(instance["data"]["a"], 2)

    instance = self.client.put(instance["ref"], {"data": {"b": 3}})

    self.assertNotIn("a", instance["data"])
    self.assertEqual(instance["data"]["b"], 3)

  def test_patch(self):
    self._create_class()
    instance = self._create_instance()
    instance = self.client.patch(instance["ref"], {"data": {"a": 1}})
    instance = self.client.patch(instance["ref"], {"data": {"b": 2}})
    self.assertEqual(instance["data"], {"a": 1, "b": 2})

  def test_delete(self):
    cls_ref = self._create_class()["ref"]
    self.client.delete(cls_ref)
    self.assertRaises(NotFound, lambda: self.client.get(cls_ref))
