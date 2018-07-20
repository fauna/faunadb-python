from faunadb.client import FaunaClient
from faunadb.errors import UnexpectedError
from tests.helpers import FaunaTestCase

class ClientTest(FaunaTestCase):

  def test_ping(self):
    old_time = self.client.last_txn_time.time
    self.assertEqual(self.client.ping("node"), "Scope node is OK")
    new_time = self.client.last_txn_time.time

    self.assertEqual(old_time, new_time) # client.ping should not update last-txn-time

  def test_last_txn_time(self):
    old_time = self.client.last_txn_time.time
    self.client.query({})
    new_time = self.client.last_txn_time.time

    self.assertTrue(old_time < new_time) # client.query should update last-txn-time

  def test_error_on_closed_client(self):
    client = FaunaClient(secret="secret")
    client.__del__()
    self.assertRaisesRegexCompat(UnexpectedError,
                                 "Cannnot create a session client from a closed session",
                                 lambda: client.new_session_client(secret="new_secret"))
