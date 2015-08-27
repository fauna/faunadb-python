from itertools import izip_longest

from faunadb.errors import NotFound
from faunadb.model.model import Model
from faunadb.model.field import Field
from faunadb.model.builtin import Class, Database, Index, Key, ClassIndex
from faunadb.objects import Ref
from faunadb import query

from test_case import FaunaTestCase

class BuiltinTest(FaunaTestCase):
  def setUp(self):
    super(BuiltinTest, self).setUp()

  def test_database(self):
    name = "builtin_test_database"
    db = Database(self.root_client, name=name, api_version="2.0")
    assert db.name == name
    assert db.api_version == "2.0"

    db.save()
    assert db.is_new_instance() == False
    ref = db.ref
    assert ref == Ref("databases", name)

    db.delete()

    # TODO: see test_database_existence.
    self.assertRaises(NotFound, lambda: self.root_client.get(ref))

  # See core issue #1975.
  def test_database_existence(self):
    q = query.exists(Ref("databases", "not_a_real_database_name"))
    # assert self.root_client.query(q) == False

  def test_key(self):
    key = Key(self.root_client, database=self.database, role="server")
    key.save()
    assert key.is_new_instance() == False
    assert len(key.hashed_secret) > 0

  def test_custom_field(self):
    Key.x = Field()
    key = Key(self.root_client, database=self.database, role="server", x=3)
    key.save()
    assert Key.get(self.root_client, key.ref).x == 3

  def test_class(self):
    class C(Model):
      __fauna_class_name__ = "c"
      x = Field()
    Class.create_for_model(self.client, C)

    cls = Class.get_for_model(self.client, C)
    assert not cls.is_new_instance()
    assert cls.history_days > 0
    assert cls.name == "c"

    cls.permissions = "public"
    cls.save()

    assert cls.permissions == "public"
    assert Class.get_for_model(self.client, C).permissions == "public"

  def test_index(self):
    class C(Model):
      __fauna_class_name__ = "cs"
      x = Field()
    Class.create_for_model(self.client, C)

    idx = Index.create_for_model(self.client, C, "cs_by_x", "x")
    assert Index.get_for_name(self.client, "cs_by_x") == idx

    c1 = C.create(self.client, x=1)
    C.create(self.client, x=2)
    c2 = C.create(self.client, x=1)

    p = C.page_index(idx, 1)
    assert p.data == [c1, c2]

    assert list(C.iter_index(idx, 1)) == [c1, c2]


  def test_multi_index(self):
    class D(Model):
      __fauna_class_name__ = "ds"
      x = Field()
      y = Field()
    Class.create_for_model(self.client, D)

    idx = Index.create_for_model(
      self.client,
      D,
      "ds_by_x_y",
      [{"path": "data.x"}, {"path": "data.y"}])
    idx.save()

    d11 = D.create(self.client, x=1, y=1)
    D.create(self.client, x=1, y=2)
    D.create(self.client, x=2, y=1)

    assert D.page_index(idx, [1, 1]).data == [d11]

  def test_class_index(self):
    class M(Model):
      __fauna_class_name__ = "test_list_model"
      number = Field()
    Class.create_for_model(self.client, M)

    idx = ClassIndex.create_for_model(self.client, M)
    assert ClassIndex.get_for_model(self.client, M) == idx

    ms = [M(self.client, number=i) for i in range(100)]
    for m in ms:
      m.save()

    ms_set = idx.match()
    page = M.page(self.client, ms_set, size=2)
    assert page.data == [ms[0], ms[1]]
    page2 = M.page(self.client, ms_set, size=2, after=page.after)
    assert page2.data == [ms[2], ms[3]]

    # List of all Ms should be exactly 100 in length; use izip_longest to be sure.
    for i, m in izip_longest(range(100), M.page_iter(self.client, ms_set)):
      assert m.number == i
