import sys
import os
import platform
from faunadb.client import FaunaClient
from faunadb.errors import UnexpectedError
from tests.helpers import FaunaTestCase
from faunadb import __version__ as pkg_version, __api_version__ as api_version

class ClientTest(FaunaTestCase):

  def test_ping(self):
    old_time = self.client.get_last_txn_time()
    self.assertEqual(self.client.ping("node"), "Scope node is OK")
    new_time = self.client.get_last_txn_time()
    self.assertEqual(old_time, new_time) # client.ping should not update last-txn-time

  def test_ping_using_endpoint(self):
    client = self._get_client_from_endpoint()
    old_time = client.get_last_txn_time()
    self.assertEqual(client.ping("node"), "Scope node is OK")
    new_time = client.get_last_txn_time()
    self.assertEqual(old_time, new_time) # client.ping should not update last-txn-time

  def test_endpoint_normalization(self):
    endpoint = self._get_fauna_endpoint()
    endpoints = [endpoint, endpoint + "/", endpoint + "//", endpoint + "\\", endpoint + "\\\\"]
    for e in endpoints:
      client = FaunaClient(secret="secret", endpoint=e)
      self.assertEqual(client.ping("node"), "Scope node is OK")

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

  def test_runtime_env_headers(self):
    client = FaunaClient(secret="secret")
    self.assertEqual(
      client.session.headers['X-Driver-Env'],
      "driver=python-{0}; runtime=python-{1} env={2}; os={3}".format(
        pkg_version, "{0}.{1}.{2}-{3}".format(*sys.version_info),
        "Unknown", "{0}-{1}".format(platform.system(), platform.release())
      ).lower()
    )

  def test_recognized_runtime_env_headers(self):
    originalPath = os.environ["PATH"]
    os.environ["PATH"] = originalPath + ".heroku"

    client = FaunaClient(secret="secret")
    self.assertEqual(
      client.session.headers['X-Driver-Env'],
      "driver=python-{0}; runtime=python-{1} env={2}; os={3}".format(
        pkg_version, "{0}.{1}.{2}-{3}".format(*sys.version_info),
        "Heroku", "{0}-{1}".format(platform.system(), platform.release())
      ).lower()
    )

    os.environ["PATH"] = originalPath
