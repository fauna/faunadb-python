from faunadb.connection import Unauthorized
from test_case import FaunaTestCase, connection

class ConnectionTest(FaunaTestCase):
  def setUp(self):
    super(ConnectionTest, self).setUp()

  def test_get_with_invalid_key(self):
    con = connection("bad_key")
    self.assertRaises(Unauthorized, lambda: con.get("users/instances"))
