from itertools import izip_longest

from faunadb.errors import BadRequest, NotFound
from faunadb.model.model import Model
from faunadb.model.field import Field
from faunadb.model.builtin import Class, Database, Index, Key, ClassIndex
from faunadb.objects import Ref

from ..helpers import FaunaTestCase

class BuiltinTest(FaunaTestCase):
  def setUp(self):
    super(BuiltinTest, self).setUp()

    class MyModel(Model):
      __fauna_class_name__ = "mooses"
      x = Field()
    Class.create_for_model(self.client, MyModel)
    self.MyModel = MyModel

  def test_database(self):
    name = "builtin_test_database"
    db = Database(self.root_client, name=name, api_version="2.0")
    assert db.name == name
    assert db.api_version == "2.0"

    db.save()
    assert db.is_new_instance() is False
    ref = db.ref
    assert ref == Ref("databases", name)

    db.delete()

    # TODO: see test_database_existence.
    self.assertRaises(NotFound, lambda: self.root_client.get(ref))

  # TODO: See core issue #1975.
  #def test_database_existence(self):
  #  q = query.exists(Ref("databases", "not_a_real_database_name"))
  #  assert self.root_client.query(q) is False

  def test_key(self):
    database = Database.get(self.root_client, self.db_ref)
    key = Key(self.root_client, database=database.ref, role="server")
    key.save()
    assert key.is_new_instance() is False
    assert len(key.hashed_secret) > 0

  def test_custom_field(self):
    database = Database.get(self.root_client, self.db_ref)
    Key.x = Field()
    key = Key(self.root_client, database=database.ref, role="server", x=3)
    key.save()
    assert Key.get(self.root_client, key.ref).x == 3

  def test_class(self):
    cls = Class.get_for_model(self.client, self.MyModel)
    assert not cls.is_new_instance()
    assert cls.history_days > 0
    assert cls.name == self.MyModel.__fauna_class_name__

    permissions = {"read": cls.ref}
    cls.permissions = permissions
    cls.save()

    assert cls.permissions == permissions
    assert Class.get_for_model(self.client, self.MyModel).permissions == permissions

  def test_index(self):
    idx = Index.create_for_model(self.client, self.MyModel, "mooses_by_x", "x")
    assert Index.get_by_id(self.client, "mooses_by_x") == idx

    instance1 = self.MyModel.create(self.client, x=1)
    self.MyModel.create(self.client, x=2)
    instance2 = self.MyModel.create(self.client, x=1)

    assert self.MyModel.page_index(idx, 1).data == [instance1, instance2]

    assert list(self.MyModel.iter_index(idx, 1)) == [instance1, instance2]

  def test_terms_and_values(self):
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

    d11 = D.create(self.client, x=1, y=1)
    D.create(self.client, x=1, y=2)
    D.create(self.client, x=2, y=1)

    assert D.page_index(idx, [1, 1]).data == [d11]

  def test_values(self):
    class E(Model):
      __fauna_class_name__ = "es"
      x = Field()
      y = Field()
      z = Field()
    Class.create_for_model(self.client, E)

    idx = Index.create_for_model(
      self.client,
      E,
      "es_by_x_sorted",
      "x",
      values=[{"path": "data.y"}, {"path": "data.z", "reverse": True}, {"path": "ref"}])

    es = {}
    for x in range(2):
      for y in range(2):
        for z in range(2):
          es[(x, y, z)] = E.create(self.client, x=x, y=y, z=z)

    expected = [es[key] for key in [(0, 0, 1), (0, 0, 0), (0, 1, 1), (0, 1, 0)]]

    assert E.page_index(idx, 0).data == expected
    assert list(E.iter_index(idx, 0)) == expected

  def test_unique_index(self):
    class F(Model):
      __fauna_class_name__ = "fs"
      x = Field()
    Class.create_for_model(self.client, F)
    index = Index.create_for_model(self.client, F, "fs_by_x", "x", unique=True)
    instance = F.create(self.client, x=1)
    # Unique index, so can't create another one.
    self.assertRaises(BadRequest, lambda: F.create(self.client, x=1))

    assert index.get_single(1) == instance._current
    assert F.get_from_index(index, 1) == instance
    self.assertRaises(NotFound, lambda: index.get_single(2))

  def test_class_index(self):
    class M(Model):
      __fauna_class_name__ = "test_list_model"
      number = Field()
    Class.create_for_model(self.client, M)

    idx = ClassIndex.create_for_model(self.client, M)
    assert ClassIndex.get_for_model(self.client, M) == idx
    ms = [M.create(self.client, number=i) for i in range(10)]

    ms_set = idx.match()
    page = M.page(self.client, ms_set, page_size=2)
    assert page.data == [ms[0], ms[1]]
    page2 = M.page(self.client, ms_set, page_size=2, after=page.after)
    assert page2.data == [ms[2], ms[3]]

    # List of all Ms should be exactly 100 in length; use izip_longest to be sure.
    for i, m in izip_longest(range(10), M.iterator(self.client, ms_set, page_size=2)):
      assert m.number == i
