from logging import getLogger, WARNING
from os import environ
from unittest import TestCase

from faunadb.client import Client
from faunadb.errors import NotFound
from faunadb.objects import Ref
from faunadb._util import no_null_values

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
    except NotFound:
      pass

    self.root_client.post("databases", {"name": db_name})

    key = self.root_client.post("keys", {"database": self.db_ref, "role": "server"})
    self.client = get_client(key["secret"])

  def tearDown(self):
    self.root_client.delete(self.db_ref)

def get_client(secret, logger=None):
  # If None, use default instead
  args = no_null_values({"domain": _FAUNA_DOMAIN, "scheme": _FAUNA_SCHEME, "port": _FAUNA_PORT})
  return Client(secret=secret, logger=logger, **args)
