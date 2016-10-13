from faunadb.client import Client
from faunadb.objects import Ref
from faunadb.query import create
from tests.helpers import FaunaTestCase

class ClientTest(FaunaTestCase):

  def test_ping(self):
    self.assertEqual(self.client.ping("all"), "Scope all is OK")

  def _create_class(self):
    return self.client.query(create(Ref("classes"), {"name": "my_class"}))

  def _create_instance(self):
    return self.client.query(create(Ref("classes/my_class"), {}))
