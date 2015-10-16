from logging import getLogger
import re
from testfixtures import LogCapture

from faunadb.client import Client
from faunadb.errors import FaunaError, NotFound, Unauthorized
from .test_case import get_client, FaunaTestCase

class ClientTest(FaunaTestCase):
  def setUp(self):
    super(ClientTest, self).setUp()

  def test_parse_secret(self):
    assert Client._parse_secret(("user", "pass")) == ("user", "pass")
    assert Client._parse_secret("user") == ("user", "")
    assert Client._parse_secret("user:pass") == ("user", "pass")
    self.assertRaises(FaunaError, lambda: Client._parse_secret(("user", "pass", "potato")))

  def test_invalid_key(self):
    client = get_client("bad_key")
    self.assertRaises(Unauthorized, lambda: client.get(self.db_ref))

  def test_ping(self):
    assert self.client.ping() == "Scope Global is OK"
    assert self.client.ping("global") == "Scope Global is OK"
    assert self.client.ping("local") == "Scope Local is OK"
    assert self.client.ping("node") == "Scope Node is OK"
    assert self.client.ping("all") == "Scope All is OK"

  def test_get(self):
    assert isinstance(self.client.get("classes")["data"], list)

  def _create_class(self):
    return self.client.post("classes", {"name": "my_class"})

  def _create_instance(self):
    return self.client.post("classes/my_class", {})

  def test_post(self):
    cls = self._create_class()
    assert self.client.get(cls["ref"]) == cls

  def test_put(self):
    self._create_class()
    instance = self._create_instance()
    instance = self.client.put(instance["ref"], {"data": {"a": 2}})

    assert instance["data"]["a"] == 2

    instance = self.client.put(instance["ref"], {"data": {"b": 3}})

    assert "a" not in instance["data"]
    assert instance["data"]["b"] == 3

  def test_patch(self):
    self._create_class()
    instance = self._create_instance()
    instance = self.client.patch(instance["ref"], {"data": {"a": 1}})
    instance = self.client.patch(instance["ref"], {"data": {"b": 2}})
    assert instance["data"] == {"a": 1, "b": 2}

  def test_delete(self):
    cls_ref = self._create_class()["ref"]
    self.client.delete(cls_ref)
    self.assertRaises(NotFound, lambda: self.client.get(cls_ref))

  def test_logging(self):
    with LogCapture() as l:
      self.client.logger = getLogger()
      self.client.ping()
      messages = [r.getMessage() for r in l.records]
      assert messages[0] == "Fauna GET /ping"
      assert re.search("^  Credentials:", messages[1])
      assert messages[2].startswith("  Response headers: {")
      assert messages[3] == """  Response JSON: {
    "resource": "Scope Global is OK"
  }"""
      assert re.search(
        r"^  Response \(200\): API processing \d+ms, network latency \d+ms$",
        messages[4])

  def test_logging_no_auth(self):
    with LogCapture() as l:
      get_client(secret=None, logger=getLogger()).ping()
      messages = [r.getMessage() for r in l.records]
      assert messages[1] == "  Credentials: None"
