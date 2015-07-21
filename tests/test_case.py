from faunadb.client import Client
from faunadb.connection import Connection, NotFound
from faunadb.objects import Ref
from faunadb import query

from os import environ
from strgen import StringGenerator
from unittest import TestCase

_FAUNA_ROOT_KEY = environ['FAUNA_ROOT_KEY']
_FAUNA_DOMAIN = environ['FAUNA_DOMAIN']
_FAUNA_SCHEME = environ['FAUNA_SCHEME']
_FAUNA_PORT = environ['FAUNA_PORT']

class FaunaTestCase(TestCase):
  def setUp(self):
    super(FaunaTestCase, self).setUp()

    self.domain = _FAUNA_DOMAIN
    self.scheme = _FAUNA_SCHEME
    self.port = _FAUNA_PORT

    self.root_connection = connection(_FAUNA_ROOT_KEY)
    root_client = Client(self.root_connection)
    test_db = Ref("databases/faunadb-python-test")

    try:
      root_client.query(query.delete(test_db))
    except NotFound:
      pass

    root_client.query(query.create(Ref("databases"), query.quote({"name": "faunadb-python-test"})))

    def get_key(role):
      return root_client.query(
        query.create(Ref("keys"), query.quote({"database": test_db, "role": role})))["secret"]

    server_key = get_key("server")
    client_key = get_key("client")

    self.server_connection = connection(server_key)
    self.client_connection = connection(client_key)
    self.client = Client(self.server_connection)

  def tearDown(self):
    pass

def connection(secret):
  return Connection(
    domain=_FAUNA_DOMAIN,
    scheme=_FAUNA_SCHEME,
    port=_FAUNA_PORT,
    secret=secret)

def random_email():
  return "%s@example.com" % StringGenerator("[\\w]{8}").render()

def random_password():
  return StringGenerator("[\\w]{8}").render()
