from collections import namedtuple
from logging import getLogger, WARNING
from os import environ
from requests import codes
from unittest import TestCase

from faunadb.client import Client
from faunadb.errors import HttpNotFound
from faunadb.objects import Ref

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

    self.root_client = get_client(_FAUNA_ROOT_KEY)

    db_name = "faunadb-python-test"
    self.db_ref = Ref("databases", db_name)
    # TODO: See `core` issue #1975
    try:
      self.root_client.delete(self.db_ref)
    except HttpNotFound:
      pass

    self.root_client.post("databases", {"name": db_name})

    key = self.root_client.post("keys", {"database": self.db_ref, "role": "server"})
    self.client = get_client(key["secret"])

  def tearDown(self):
    self.root_client.delete(self.db_ref)


def get_client(secret, logger=None):
  args = {"domain": _FAUNA_DOMAIN, "scheme": _FAUNA_SCHEME, "port": _FAUNA_PORT}
  # If None, use default instead
  non_null_args = {k: v for k, v in args.iteritems() if v is not None}
  return Client(secret=secret, logger=logger, **non_null_args)


def mock_client(response_text, status_code=codes.ok):
  c = Client()
  c.session = _MockSession(response_text, status_code)
  return c


class _MockSession(object):
  def __init__(self, response_text, status_code):
    self.response_text = response_text
    self.status_code = status_code

  def prepare_request(self, *args):
    pass

  def send(self, *args):
    # pylint: disable=unused-argument
    return _MockResponse(self.status_code, self.response_text)


_MockResponse = namedtuple('MockResponse', ['status_code', 'text'])
