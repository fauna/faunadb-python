from faunadb.client import Client
from faunadb.errors import BadRequest
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
  return Client(
    domain=_FAUNA_DOMAIN,
    scheme=_FAUNA_SCHEME,
    port=_FAUNA_PORT,
    secret=secret)

def random_email():
  return "%s@example.com" % StringGenerator("[\\w]{8}").render()

def random_password():
  return StringGenerator("[\\w]{8}").render()
