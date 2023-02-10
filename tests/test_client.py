import sys
import os
import platform
import random
import string
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

  def test_tags_header(self):
    self.client.observer = lambda rr: self.assertCountEqual(rr.response_headers["x-fauna-tags"].split(","), ["foo=bar", "baz=biz"])
    test_tags = {
      "foo": "bar",
      "baz": "biz",
    }
    self.client.query({}, tags=test_tags)

    self.client.observer = None

  def test_invalid_tags_keys(self):
    invalid_keys = [
      "foo bar",
      "foo*bar",
      ''.join(random.choice(string.ascii_lowercase) for _ in range(41)),
    ]
    for key in invalid_keys:
      self.assertRaisesRegexCompat(Exception,
                             "One or more tag keys are invalid",
                             lambda: self.client.query({}, tags={ key: "value" }))

  def test_invalid_tags_values(self):
    invalid_values = [
      "foo bar",
      "foo*bar",
      ''.join(random.choice(string.ascii_lowercase) for _ in range(81)),
    ]
    for value in invalid_values:
      self.assertRaisesRegexCompat(Exception,
                             "One or more tag values are invalid",
                             lambda: self.client.query({}, tags={ "key": value }))

  def test_too_many_tags(self):
    too_many_keys = [ (''.join(random.choice(string.ascii_lowercase) for _ in range(10))) for _ in range(30) ]
    too_many_tags = { k: "value" for k in too_many_keys }
    self.assertRaisesRegexCompat(Exception,
                           "Tags header only supports up to 25 key-value pairs",
                           lambda: self.client.query({}, tags=too_many_tags))

  def test_traceparent_header(self):
    token = ''.join(random.choice(string.hexdigits.lower()) for _ in range(32))
    token2 = ''.join(random.choice(string.hexdigits.lower()) for _ in range(16))
    self.client.observer = lambda rr: self.assertRegexCompat(rr.response_headers["traceparent"], "^00-%s-\w{16}-\d{2}$"%(token))
    self.client.query({}, traceparent="00-%s-%s-01"%(token, token2))

    self.client.observer = None

  def test_invalid_traceparent_header(self):
    self.assertRaisesRegexCompat(Exception,
                           "Traceparent format is incorrect",
                           lambda: self.client.query({}, traceparent="foo"))

  def test_empty_traceparent_header(self):
    tp_header = None
    tp_part = None

    def _test_and_save_traceparent(rr):
      self.assertIsNotNone(rr.response_headers["traceparent"])
      nonlocal tp_header, tp_part
      tp_header = rr.response_headers["traceparent"]
      tp_part = tp_header.split('-')[1]

    self.client.observer = _test_and_save_traceparent
    self.client.query({}, traceparent=None)

    self.client.observer = lambda rr: self.assertRegexCompat(rr.response_headers["traceparent"], "^00-%s-\w{16}-\d{2}$"%(tp_part))
    self.client.query({}, traceparent=tp_header)

    self.client.observer = None
