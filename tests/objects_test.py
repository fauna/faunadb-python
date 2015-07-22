from faunadb.objects import Event, Ref, Set
from faunadb._json import parse_json, to_json
from test_case import FaunaTestCase

class ObjectsTest(FaunaTestCase):
  def setUp(self):
    super(ObjectsTest, self).setUp()

    user = Ref("users", "123")
    json_user = '{"@ref": "users/123"}'

    index = Ref("indexes", "users_by_bff")
    json_index = '{"@ref": "indexes/users_by_bff"}'

    self.object_to_json = {
      user: json_user,
      index: json_index,
      Set(user, index):
        '{"@set": {"index": %s, "match": %s}}' % (json_index, json_user)
    }

  def test_parse(self):
    for obj, json in self.object_to_json.iteritems():
      assert parse_json(json) == obj
    assert parse_json('{"@obj": {"a": 1, "b": 2}}') == {"a": 1, "b": 2}

  def test_to_json(self):
    for obj, json in self.object_to_json.iteritems():
      assert to_json(obj) == json
    assert to_json(Event(123, "create", Ref("users/123"))) == \
      '{"action": "create", "resource": {"@ref": "users/123"}, "ts": 123}'
    assert to_json(Event(123, None, None)) == '{"ts": 123}'

  def test_ref(self):
    blobs = Ref("classes/blobs")
    ref = Ref(blobs, "123")
    assert ref.to_class() == blobs
    assert ref.id() == "123"

    keys = Ref("keys")
    ref = Ref(keys, "123")
    assert ref.to_class() == keys
    assert ref.id() == "123"
