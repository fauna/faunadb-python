from io import StringIO

from faunadb.client_logger import logger
from faunadb.query import create, create_collection
from tests.helpers import FaunaTestCase

class ClientLoggerTest(FaunaTestCase):
  @classmethod
  def setUpClass(cls):
    super(ClientLoggerTest, cls).setUpClass()
    cls.collection_ref = cls.client.query(create_collection({"name": "logging_tests"}))["ref"]

  def test_logging(self):
    logged = self.get_logged(lambda client: client.ping())

    read_line = StringIO(logged).readline
    self.assertEqual(read_line(), "Fauna GET /ping\n")
    self.assertEqual(read_line(), "  Response headers: {\n")
    # Skip through headers
    while True:
      line = read_line()
      if not line.startswith("    "):
        self.assertEqual(line, "  }\n")
        break
    self.assertEqual(read_line(), "  Response JSON: {\n")
    self.assertEqual(read_line(), '    "resource": "Scope write is OK"\n')
    self.assertEqual(read_line(), "  }\n")
    self.assertRegexCompat(
      read_line(),
      r"^  Response \(200\): Network latency \d+ms\n$")

  def test_request_content(self):
    logged = self.get_logged(lambda client: client.query(create(self.collection_ref, {"data": {}})))

    read_line = StringIO(logged).readline
    self.assertEqual(read_line(), "Fauna POST /\n")
    self.assertEqual(read_line(), "  Request JSON: {\n")
    self.assertEqual(read_line(), '    "create": {\n')
    self.assertEqual(read_line(), '      "@ref": {\n')
    self.assertEqual(read_line(), '        "collection": {\n')
    self.assertEqual(read_line(), '          "@ref": {\n')
    self.assertEqual(read_line(), '            "id": "collections"\n')
    self.assertEqual(read_line(), '          }\n')
    self.assertEqual(read_line(), '        }, \n')
    self.assertEqual(read_line(), '        "id": "logging_tests"\n')
    self.assertEqual(read_line(), '      }\n')
    self.assertEqual(read_line(), '    }, \n')
    self.assertEqual(read_line(), '    "params": {\n')
    self.assertEqual(read_line(), '      "object": {\n')
    self.assertEqual(read_line(), '        "data": {\n')
    self.assertEqual(read_line(), '          "object": {}\n')
    self.assertEqual(read_line(), '        }\n')
    self.assertEqual(read_line(), '      }\n')
    self.assertEqual(read_line(), '    }\n')
    self.assertEqual(read_line(), '  }\n')
    # Ignore the rest

  def test_url_query(self):
    logged = self.get_logged(lambda client: client.ping('node', 250))
    self.assertEqual(logged.split('\n')[0], "Fauna GET /ping?scope=node&timeout=250")

  def get_logged(self, client_action):
    logged_box = []
    client = self.root_client.new_session_client(secret=self.server_key,
                                                 observer=logger(logged_box.append))
    client_action(client)
    return logged_box[0]
