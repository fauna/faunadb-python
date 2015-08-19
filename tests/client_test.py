from faunadb.errors import NotFound, Unauthorized
from faunadb.objects import Ref
from test_case import get_client, FaunaTestCase, random_email, random_password

def _assert_is_headers(headers):
  assert "content-type" in headers

class ClientTest(FaunaTestCase):
  def setUp(self):
    super(ClientTest, self).setUp()

  def _create_user(self):
    return self.client.post("users", {
      "name": "Arawn",
      "email": random_email(),
      "password": random_password()
    }).resource

  def test_get_with_invalid_key(self):
    client = get_client("bad_key")
    self.assertRaises(Unauthorized, lambda: client.get("users/instances"))

  def test_ping(self):
    assert self.client.ping().resource == 'Scope Global is OK'
    assert self.client.ping('global').resource == 'Scope Global is OK'
    assert self.client.ping('local').resource == 'Scope Local is OK'
    assert self.client.ping('node').resource == 'Scope Node is OK'
    assert self.client.ping('all').resource == 'Scope All is OK'

  def test_get(self):
    self.client.get("users")

  def test_post(self):
    self._create_user()

  def test_put(self):
    user = self._create_user()
    user = self.client.put(user["ref"], {"data": {"pockets": 2}}).resource

    assert user["data"]["pockets"] == 2

    user = self.client.put(user["ref"], {"data": {"apples": 3}}).resource

    assert "pockets" not in user["data"]
    assert user["data"]["apples"] == 3

  def test_patch(self):
    user = self._create_user()
    user = self.client.patch(user["ref"], {"data": {"pockets": 2}}).resource
    user = self.client.patch(user["ref"], {"data": {"apples": 3}}).resource

    assert user["data"]["pockets"] == 2
    assert user["data"]["apples"] == 3

  def test_delete(self):
    user = self._create_user()
    headers = self.client.delete(user["ref"]).headers
    _assert_is_headers(headers)
    self.assertRaises(NotFound, lambda: self.client.get(user["ref"]))

  def test_refs(self):
    user1 = self.client.post("users", {"name": "One"}).resource
    assert isinstance(user1["ref"], Ref)
    user2 = self.client.post("users", {"data": {"best_friend": user1["ref"]}}).resource
    assert user2["data"]["best_friend"] == user1["ref"]

  def test_get_with_headers(self):
    headers = self.client.get("users").headers
    assert headers["content-type"] == "application/json;charset=utf-8"
