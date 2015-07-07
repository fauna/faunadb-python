from faunadb.client import Client
from faunadb.connection import NotFound
from faunadb.objects import Ref
from test_case import FaunaTestCase, random_email, random_password

class ClientTest(FaunaTestCase):
  def setUp(self):
    super(ClientTest, self).setUp()
    self.client = Client(self.server_connection)
    self.client_client = Client(self.client_connection)

  def test_get(self):
    self.client.get("users")

  def test_post(self):
    return self.client.post("users", {
      "name": "Arawn",
      "email": random_email(),
      "password": random_password()
    })

  def test_put(self):
    user = self.test_post()
    user = self.client.put(user["ref"], {"data": {"pockets": 2}})

    assert user["data"]["pockets"] == 2

    user = self.client.put(user["ref"], {"data": {"apples": 3}})

    assert "pockets" not in user["data"]
    assert user["data"]["apples"] == 3

  def test_patch(self):
    user = self.test_post()
    user = self.client.patch(user["ref"], {"data": {"pockets": 2}})
    user = self.client.patch(user["ref"], {"data": {"apples": 3}})

    assert user["data"]["pockets"] == 2
    assert user["data"]["apples"] == 3

  def test_delete(self):
    user = self.test_post()
    self.client.delete(user["ref"])
    self.assertRaises(NotFound, lambda: self.client.get(user["ref"]))

  def test_refs(self):
    user1 = self.client.post("users", {"name": "One"})
    assert isinstance(user1["ref"], Ref)
    user2 = self.client.post("users", {"data": {"best_friend": user1["ref"]}})
    assert user2["data"]["best_friend"] == user1["ref"]

  def test_get_with_headers(self):
    headers = self.client.get_with_headers("users").headers
    assert headers["content-type"] == "application/json;charset=utf-8"
