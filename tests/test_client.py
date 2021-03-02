from faunadb.client import FaunaClient
from faunadb.errors import UnexpectedError
from tests.helpers import FaunaTestCase

class ClientTest(FaunaTestCase):

  def test_ping(self):
    old_time = self.client.get_last_txn_time()
    self.assertEqual(self.client.ping("node"), "Scope node is OK")
    new_time = self.client.get_last_txn_time()

    self.assertEqual(old_time, new_time) # client.ping should not update last-txn-time

  def test_default_query_timeout(self):
    client = FaunaClient(secret="secret")
    self.assertEqual(client.get_query_timeout(), 60000)

  def test_query_timeout(self):
    client = FaunaClient(secret="secret", query_timeout_ms=5000)
    self.assertEqual(client.get_query_timeout(), 5000)
    

  def test_last_txn_time(self):
    old_time = self.client.get_last_txn_time()
    self.client.query({})
    new_time = self.client.get_last_txn_time()

    self.assertTrue(old_time < new_time) # client.query should update last-txn-time

  def test_last_txn_time_upated(self):
    first_seen = self.client.get_last_txn_time()

    new_time = first_seen - 12000
    self.client.sync_last_txn_time(new_time)
    self.assertEqual(self.client.get_last_txn_time(), first_seen) # last-txn can not be smaller

    new_time = first_seen + 12000
    self.client.sync_last_txn_time(new_time)
    self.assertEqual(self.client.get_last_txn_time(), new_time) # last-txn can move forward

  def test_error_on_closed_client(self):
    client = FaunaClient(secret="secret")
    client.__del__()
    self.assertRaisesRegexCompat(UnexpectedError,
                                 "Cannnot create a session client from a closed session",
                                 lambda: client.new_session_client(secret="new_secret"))
