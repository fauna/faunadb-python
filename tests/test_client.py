from io import StringIO

from faunadb.client import Client
from faunadb.client_logger import logger
from faunadb.errors import NotFound
from tests.helpers import FaunaTestCase

class ClientTest(FaunaTestCase):
  def test_parse_secret(self):
    self.assertEqual(Client._parse_secret(("user", "pass")), ("user", "pass"))
    self.assertEqual(Client._parse_secret("user"), ("user", ""))
    self.assertEqual(Client._parse_secret("user:pass"), ("user", "pass"))
    self.assertRaises(ValueError, lambda: Client._parse_secret(("user", "pass", "potato")))

  def test_ping(self):
    self.assertEqual(self.client.ping(), "Scope Global is OK")
    self.assertEqual(self.client.ping("global"), "Scope Global is OK")
    self.assertEqual(self.client.ping("local"), "Scope Local is OK")
    self.assertEqual(self.client.ping("node"), "Scope Node is OK")
    self.assertEqual(self.client.ping("all"), "Scope All is OK")

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

  def test_logging(self):
    logged_box = []
    client = self.get_client(observer=logger(logged_box.append))
    client.ping()
    logged = logged_box[0]

    read_line = StringIO(logged).readline
    self.assertEqual(read_line(), "Fauna GET /ping\n")
    self.assertRegexCompat(read_line(), r"^  Credentials:")
    self.assertEqual(read_line(), "  Response headers: {\n")
    # Skip through headers
    while True:
      line = read_line()
      if not line.startswith("    "):
        self.assertEqual(line, "  }\n")
        break
    self.assertEqual(read_line(), "  Response JSON: {\n")
    self.assertEqual(read_line(), '    "resource": "Scope Global is OK"\n')
    self.assertEqual(read_line(), "  }\n")
    self.assertRegexCompat(
      read_line(),
      r"^  Response \(200\): API processing \d+ms, network latency \d+ms\n$")
