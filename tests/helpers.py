import string
import random
import warnings
from collections import namedtuple
from logging import getLogger, WARNING
from os import environ
from unittest import TestCase
# pylint: disable=redefined-builtin
from builtins import object, range
from requests import codes

from faunadb._json import to_json, parse_json
from faunadb.client import FaunaClient
from faunadb import query

_FAUNA_ROOT_KEY = environ["FAUNA_ROOT_KEY"]
# If None, these have defaults in FaunaClient.
_FAUNA_DOMAIN = environ.get("FAUNA_DOMAIN")
_FAUNA_SCHEME = environ.get("FAUNA_SCHEME")
_FAUNA_PORT = environ.get("FAUNA_PORT")

_FAUNA_QUERY_TIMEOUT_MS = environ.get("FAUNA_QUERY_TIMEOUT_MS")

class FaunaTestCase(TestCase):
  @classmethod
  def setUpClass(cls):
    super(FaunaTestCase, cls).setUpClass()

    # Turn off annoying logging about reset connections.
    getLogger("requests").setLevel(WARNING)

    cls.root_client = cls._get_client()

    rnd = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
    cls.db_name = "faunadb-python-test" + rnd
    cls.db_ref = query.database(cls.db_name)

    if cls.root_client.query(query.exists(cls.db_ref)):
      cls.root_client.query(query.delete(cls.db_ref))

    cls.root_client.query(query.create_database({"name": cls.db_name}))

    cls.server_key = cls.root_client.query(
      query.create_key({"database": cls.db_ref, "role": "server"}))["secret"]
    cls.client = cls.root_client.new_session_client(secret=cls.server_key)

    cls.admin_key = cls.root_client.query(
      query.create_key({"database": cls.db_ref, "role": "admin"}))["secret"]
    cls.admin_client = cls.root_client.new_session_client(secret=cls.admin_key)

  @classmethod
  def tearDownClass(cls):
    cls.root_client.query(query.delete(cls.db_ref))

  def assertJson(self, obj, json):
    self.assertToJson(obj, json)
    self.assertParseJson(obj, json)

  def assertToJson(self, obj, json):
    self.assertEqual(to_json(obj, sort_keys=True), json)

  def assertParseJson(self, obj, json):
    self.assertEqual(parse_json(json), obj)

  def assertRegexCompat(self, text, regex, msg=None):
    # pylint: disable=deprecated-method
    with warnings.catch_warnings():
      # Deprecated in 3.x but 2.x does not have it under the new name.
      warnings.filterwarnings("ignore", category=DeprecationWarning)
      self.assertRegexpMatches(text, regex, msg=msg)

  def assertRaisesRegexCompat(self, exception, regexp, callable, *args, **kwds):
    # pylint: disable=deprecated-method
    with warnings.catch_warnings():
      # Deprecated in 3.x but 2.x does not have it under the new name.
      warnings.filterwarnings("ignore", category=DeprecationWarning)
      self.assertRaisesRegexp(exception, regexp, callable, *args, **kwds)

  @classmethod
  def _get_client(cls):
    args = {
      "domain": _FAUNA_DOMAIN,
      "scheme": _FAUNA_SCHEME,
      "port": _FAUNA_PORT,
      "query_timeout_ms": _FAUNA_QUERY_TIMEOUT_MS
    }
    # If None, use default instead
    non_null_args = {k: v for k, v in args.items() if v is not None}
    return FaunaClient(secret=_FAUNA_ROOT_KEY, **non_null_args)

  @classmethod
  def _get_fauna_endpoint(cls):
    return "%s://%s:%s" % (_FAUNA_SCHEME, _FAUNA_DOMAIN, _FAUNA_PORT)

  @classmethod
  def _get_client_from_endpoint(cls):
    args = {
      "endpoint": cls._get_fauna_endpoint(),
      "domain": "bad domain",
      "scheme": "bad scheme",
      "port": "bad port",
      "query_timeout_ms": _FAUNA_QUERY_TIMEOUT_MS
    }
    # If None, use default instead
    non_null_args = {k: v for k, v in args.items() if v is not None}
    return FaunaClient(secret=_FAUNA_ROOT_KEY, **non_null_args)

  def assert_raises(self, exception_class, action):
    """Like self.assertRaises and returns the exception too."""
    with self.assertRaises(exception_class) as cm:
      action()
    return cm.exception


def mock_client(response_text, status_code=codes.ok):
  c = FaunaClient(secret=None)
  c.session = _MockSession(response_text, status_code)
  return c


class _MockSession(object):
  def __init__(self, response_text, status_code):
    self.response_text = response_text
    self.status_code = status_code

  def close(self):
    pass

  def prepare_request(self, *args):
    pass

  def send(self, *args):
    # pylint: disable=unused-argument
    return _MockResponse(self.status_code, self.response_text, {})


_MockResponse = namedtuple('MockResponse', ['status_code', 'text', 'headers'])
