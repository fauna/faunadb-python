from faunadb.client import Client
from faunadb.connection import Connection, NotFound
from faunadb.objects import Ref

from os import environ
from strgen import StringGenerator
from unittest import TestCase

_FAUNA_ROOT_KEY = environ['FAUNA_ROOT_KEY']
_FAUNA_DOMAIN = environ['FAUNA_DOMAIN']
_FAUNA_SCHEME = environ['FAUNA_SCHEME']
_FAUNA_PORT = environ['FAUNA_PORT']

class FaunaTestCase(TestCase):
  def setUp(self):
    self.domain = _FAUNA_DOMAIN
    self.scheme = _FAUNA_SCHEME
    self.port = _FAUNA_PORT

    self.root_connection = connection(_FAUNA_ROOT_KEY)
    root_client = Client(self.root_connection)
    test_db = Ref("databases/faunadb-python-test")

    try:
      root_client.delete(test_db.ref_str)
    except NotFound:
      pass
    root_client.post("databases", {"name": "faunadb-python-test"})

    server_key = root_client.post(
      "keys",
      {"database": test_db, "role": "server"})["secret"]
    client_key = root_client.post(
      "keys",
      {"database": test_db, "role": "client"})["secret"]

    self.server_connection = connection(server_key)
    self.client_connection = connection(client_key)

    super(FaunaTestCase, self).setUp()

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
