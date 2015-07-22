from faunadb.connection import NotFound
from faunadb.errors import InvalidQuery
from faunadb.objects import Ref
from faunadb import query
from test_case import FaunaTestCase, random_email, random_password

class QueryTest(FaunaTestCase):
  def setUp(self):
    super(QueryTest, self).setUp()

  def _create_user(self):
    data = query.object(name="Arawn", email=random_email(), password=random_password())
    return self.client.query(query.create(Ref('users'), data)).resource

  def test_post(self):
    self._create_user()

  def test_put(self):
    user = self._create_user()
    data = query.object(data=query.object(pockets=2))
    user = self.client.query(query.replace(user["ref"], data)).resource

    assert user["data"]["pockets"] == 2

    data = query.object(data=query.object(apples=3))
    user = self.client.query(query.replace(user["ref"], data)).resource

    assert "pockets" not in user["data"]
    assert user["data"]["apples"] == 3

  def test_patch(self):
    user = self._create_user()
    data = query.object(data=query.object(pockets=2))
    user = self.client.query(query.update(user["ref"], data)).resource
    data = query.object(data=query.object(apples=3))
    user = self.client.query(query.update(user["ref"], data)).resource

    assert user["data"]["pockets"] == 2
    assert user["data"]["apples"] == 3

  def test_delete(self):
    user = self._create_user()
    self.client.query(query.delete(user["ref"]))
    self.assertRaises(NotFound, lambda: self.client.query(query.get(user["ref"])))

  def test_allowed_params(self):
    user = self._create_user()
    copy = self.client.query(query.get(user["ref"], {"ts": user["ts"]})).resource
    assert user == copy
    self.assertRaises(InvalidQuery, lambda: query.get(user["ref"], {"tee ess": 123}))
