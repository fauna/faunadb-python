from io import StringIO

from faunadb.client_logger import logger
from faunadb.objects import Ref
from faunadb.query import create
from tests.helpers import FaunaTestCase

class ClientLoggerTest(FaunaTestCase):
  def setUp(self):
    super(ClientLoggerTest, self).setUp()
    self.class_ref = self.client.query(create(Ref("classes"), {"name": "logging_tests"}))["ref"]

  def test_logging(self):
    logged = self.get_logged(lambda client: client.ping())

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
    self.assertEqual(read_line(), '    "resource": "Scope global is OK"\n')
    self.assertEqual(read_line(), "  }\n")
    self.assertRegexCompat(
      read_line(),
      r"^  Response \(200\): Network latency \d+ms\n$")

  def test_request_content(self):
    logged = self.get_logged(lambda client: client.query(create(self.class_ref, {"data": {}})))

    read_line = StringIO(logged).readline
    self.assertEqual(read_line(), "Fauna POST /\n")
    self.assertRegexCompat(read_line(), r"^  Credentials:")
    self.assertEqual(read_line(), "  Request JSON: {\n")
    self.assertEqual(read_line(), '    "create": {\n')
    self.assertEqual(read_line(), '      "@ref": "classes/logging_tests"\n')
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
    logged = self.get_logged(lambda client: client.ping("all", 100))
    self.assertEqual(logged.split('\n')[0], "Fauna GET /ping?scope=all&timeout=100")

  def get_logged(self, client_action):
    logged_box = []
    client = self.get_client(observer=logger(logged_box.append))
    client_action(client)
    return logged_box[0]
