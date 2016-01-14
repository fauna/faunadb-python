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
from faunadb.client import Client
from faunadb.errors import BadRequest
from faunadb.objects import Ref
from faunadb import query

_FAUNA_ROOT_KEY = environ["FAUNA_ROOT_KEY"]
# If None, these have defaults in Client.
_FAUNA_DOMAIN = environ.get("FAUNA_DOMAIN")
_FAUNA_SCHEME = environ.get("FAUNA_SCHEME")
_FAUNA_PORT = environ.get("FAUNA_PORT")

class FaunaTestCase(TestCase):
  def setUp(self):
    super(FaunaTestCase, self).setUp()

    # Turn off annoying logging about reset connections.
    getLogger("requests").setLevel(WARNING)

    self.root_client = self.get_client(secret=_FAUNA_ROOT_KEY)

    rnd = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
    db_name = "faunadb-python-test" + rnd
    self.db_ref = Ref("databases", db_name)
    # TODO: See `core` issue #1975
    try:
      self.root_client.query(query.delete(self.db_ref))
    except BadRequest:
      pass

    self.root_client.query(query.create(Ref("databases"), query.object(name=db_name)))

    self.server_key = self.root_client.query(
      query.create(Ref("keys"), query.object(database=self.db_ref, role="server")))["secret"]
    self.client = self.get_client()

  def tearDown(self):
    self.root_client.query(query.delete(self.db_ref))

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

  def get_client(self, secret=None, observer=None):
    if secret is None:
      secret = self.server_key

    args = {"domain": _FAUNA_DOMAIN, "scheme": _FAUNA_SCHEME, "port": _FAUNA_PORT}
    # If None, use default instead
    non_null_args = {k: v for k, v in args.items() if v is not None}
    return Client(secret=secret, observer=observer, **non_null_args)

  def assert_raises(self, exception_class, action):
    """Like self.assertRaises and returns the exception too."""
    with self.assertRaises(exception_class) as cm:
      action()
    return cm.exception


def mock_client(response_text, status_code=codes.ok):
  c = Client()
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
