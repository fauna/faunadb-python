from faunadb.client import Client
from faunadb.errors import NotFound
from faunadb.objects import Ref
from faunadb.query import create, quote
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
    return self.client.query(create(Ref("classes"), quote({"name": "my_class"})))

  def _create_instance(self):
    return self.client.query(create(Ref("classes/my_class"), quote({})))
