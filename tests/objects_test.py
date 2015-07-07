from faunadb.objects import Event, Obj, Ref, Set
from faunadb._json import parse_json, to_json
from test_case import FaunaTestCase

class ClientTest(FaunaTestCase):
  def setUp(self):
    super(ClientTest, self).setUp()

    user = Ref("users/123")
    json_user = '{"@ref": "users/123"}'

    index = Ref("indexes/users_by_bff")
    json_index = '{"@ref": "indexes/users_by_bff"}'

    self.object_to_json = {
      user: json_user,
      index: json_index,
      Set(user, index):
        '{"@set": {"index": %s, "match": %s}}' % (json_index, json_user)
    }

  def test_parse(self):
    for obj, json in self.object_to_json.iteritems():
      print parse_json(json)
      print obj
      assert parse_json(json) == obj
    assert parse_json('{"@obj": {"a": 1, "b": 2}}') == Obj(a=1, b=2)

  def test_to_json(self):
    for obj, json in self.object_to_json.iteritems():
      assert to_json(obj) == json
    assert to_json(Obj(a=1, b=2)) == '{"object": {"a": 1, "b": 2}}'
    assert to_json(Event(123, "create", Ref("users/123"))) == \
      '{"action": "create", "resource": {"@ref": "users/123"}, "ts": 123}'
    assert to_json(Event(123, None, None)) == '{"ts": 123}'
