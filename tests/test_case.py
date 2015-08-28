from faunadb.client import Client
from faunadb.errors import NotFound
from faunadb.objects import Ref
from faunadb.model.builtin import Database, Key

from logging import getLogger, WARNING
from os import environ
from strgen import StringGenerator
from unittest import TestCase

_FAUNA_ROOT_KEY = environ['FAUNA_ROOT_KEY']
# If None, these have defaults in Client.
_FAUNA_DOMAIN = environ.get('FAUNA_DOMAIN')
_FAUNA_SCHEME = environ.get('FAUNA_SCHEME')
_FAUNA_PORT = environ.get('FAUNA_PORT')

class FaunaTestCase(TestCase):
  def setUp(self):
    super(FaunaTestCase, self).setUp()

    # Turn off annoying logging about reset connections.
    getLogger("requests").setLevel(WARNING)

    self.root_client = get_client(_FAUNA_ROOT_KEY)

    db_name = "faunadb-python-test"
    # TODO: See builtin_test test_database_existence
    try:
      self.root_client.delete(Ref("databases", db_name))
    except NotFound:
      pass

    self.database = Database.create(self.root_client, name=db_name)

    def get_key(role):
      key = Key(self.root_client, database=self.database, role=role)
      key.save()
      return key.secret

    self.client = get_client(get_key("server"))

  def tearDown(self):
    self.database.delete()

def get_client(secret):
  args = {"domain": _FAUNA_DOMAIN, "scheme": _FAUNA_SCHEME, "port": _FAUNA_PORT}
  # If None, use default instead
  non_null_args = {k: v for k, v in args.iteritems() if v is not None}
  return Client(secret=secret, **non_null_args)

def random_email():
  return "%s@example.com" % StringGenerator("[\\w]{8}").render()

def random_password():
  return StringGenerator("[\\w]{8}").render()
