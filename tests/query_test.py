from faunadb.connection import NotFound
from faunadb.client import Client
from faunadb import query
from faunadb.objects import Obj, Ref
from test_case import FaunaTestCase, random_email, random_password

class QueryTest(FaunaTestCase):
  def setUp(self):
    super(QueryTest, self).setUp()
    self.client = Client(self.server_connection)
    self.client_client = Client(self.client_connection)

  def test_post(self):
    data = Obj(name="Arawn", email=random_email(), password=random_password())
    return self.client.query(query.create(Ref('users'), data))

  def test_put(self):
    user = self.test_post()
    data = Obj(data=Obj(pockets=2))
    user = self.client.query(query.replace(user["ref"], data))

    assert user["data"]["pockets"] == 2

    data = Obj(data=Obj(apples=3))
    user = self.client.query(query.replace(user["ref"], data))

    assert "pockets" not in user["data"]
    assert user["data"]["apples"] == 3

  def test_patch(self):
    user = self.test_post()
    data = Obj(data=Obj(pockets=2))
    user = self.client.query(query.update(user["ref"], data))
    data = Obj(data=Obj(apples=3))
    user = self.client.query(query.update(user["ref"], data))

    assert user["data"]["pockets"] == 2
    assert user["data"]["apples"] == 3

  def test_delete(self):
    user = self.test_post()
    self.client.query(query.delete(user["ref"]))
    self.assertRaises(NotFound, lambda: self.client.query(query.get(user["ref"])))
