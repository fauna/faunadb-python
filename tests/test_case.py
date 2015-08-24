from faunadb.client import Client
from faunadb.errors import BadRequest
from faunadb.objects import Ref
from faunadb import query

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
    test_db = Ref("databases/faunadb-python-test")

    try:
      self.root_client.query(query.delete(test_db))
    except BadRequest:
      pass

    create_db = query.create(Ref("databases"), query.quote({"name": "faunadb-python-test"}))
    self.root_client.query(create_db)

    def get_key(role):
      db = query.quote({"database": test_db, "role": role})
      response = self.root_client.query(query.create(Ref("keys"), db))
      return response.resource["secret"]

    server_key = get_key("server")

    self.client = get_client(server_key)

  def tearDown(self):
    pass

def get_client(secret):
  args = {"domain": _FAUNA_DOMAIN, "scheme": _FAUNA_SCHEME, "port": _FAUNA_PORT}
  # If None, use default instead
  non_null_args = {k: v for k, v in args.iteritems() if v is not None}
  return Client(secret=secret, **non_null_args)

def random_email():
  return "%s@example.com" % StringGenerator("[\\w]{8}").render()

def random_password():
  return StringGenerator("[\\w]{8}").render()
