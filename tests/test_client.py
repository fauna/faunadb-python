from faunadb.client import FaunaClient
from faunadb.errors import UnexpectedError
from tests.helpers import FaunaTestCase

class ClientTest(FaunaTestCase):

  def test_ping(self):
    self.assertEqual(self.client.ping("all"), "Scope all is OK")

  def test_error_on_closed_client(self):
    client = FaunaClient(secret="secret")
    client.__del__()
    self.assertRaisesRegexCompat(UnexpectedError,
                                 "Cannnot create a session client from a closed session",
                                 lambda: client.new_session_client(secret="new_secret"))
