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
    self.assertEqual(db.name, name)
    self.assertEqual(db.api_version, "2.0")

    db.save()
    self.assertFalse(db.is_new_instance())
    ref = db.ref
    self.assertEqual(ref, Ref("databases", name))

    db.delete()

    # TODO: see test_database_existence.
    self.assertRaises(NotFound, lambda: self.root_client.get(ref))

  # TODO: See core issue #1975.
  #def test_database_existence(self):
  #  q = query.exists(Ref("databases", "not_a_real_database_name"))
  #  self.assertFalse(self.root_client.query(q))

  def test_key(self):
    database = Database.get(self.root_client, self.db_ref)
    key = Key(self.root_client, database=database.ref, role="server")
    key.save()
    self.assertFalse(key.is_new_instance())
    self.assertGreater(len(key.hashed_secret), 0)

  def test_custom_field(self):
    database = Database.get(self.root_client, self.db_ref)
    Key.x = Field()
    key = Key(self.root_client, database=database.ref, role="server", x=3)
    key.save()
    self.assertEqual(Key.get(self.root_client, key.ref).x, 3)

  def test_class(self):
    cls = Class.get_for_model(self.client, self.MyModel)
    self.assertFalse(cls.is_new_instance())
    self.assertGreater(cls.history_days, 0)
    self.assertEqual(cls.name, self.MyModel.__fauna_class_name__)

    permissions = {"read": cls.ref}
    cls.permissions = permissions
    cls.save()

    self.assertEqual(cls.permissions, permissions)
    self.assertEqual(Class.get_for_model(self.client, self.MyModel).permissions, permissions)

  def test_index(self):
    idx = Index.create_for_model(self.client, self.MyModel, "mooses_by_x", "x")
    self.assertEqual(Index.get_by_id(self.client, "mooses_by_x"), idx)

    instance1 = self.MyModel.create(self.client, x=1)
    self.MyModel.create(self.client, x=2)
    instance2 = self.MyModel.create(self.client, x=1)

    self.assertEqual(self.MyModel.page_index(idx, 1).data, [instance1, instance2])

    self.assertEqual(list(self.MyModel.iter_index(idx, 1)), [instance1, instance2])

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

    self.assertEqual(D.page_index(idx, [1, 1]).data, [d11])

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

    self.assertEqual(E.page_index(idx, 0).data, expected)
    self.assertEqual(list(E.iter_index(idx, 0)), expected)

    # Fails if {"path": "ref"} is not at the end.
    idx2 = Index.create_for_model(self.client, E, "bad_index", "x", values=[{"path": "data.y"}])
    self.assertRaises(AssertionError, lambda: E.page_index(idx2, 0))

  def test_unique_index(self):
    class F(Model):
      __fauna_class_name__ = "fs"
      x = Field()
    Class.create_for_model(self.client, F)
    index = Index.create_for_model(self.client, F, "fs_by_x", "x", unique=True)
    instance = F.create(self.client, x=1)
    # Unique index, so can't create another one.
    self.assertRaises(BadRequest, lambda: F.create(self.client, x=1))

    self.assertEqual(index.get_single(1), instance._current)
    self.assertEqual(F.get_from_index(index, 1), instance)
    self.assertRaises(NotFound, lambda: index.get_single(2))

  def test_class_index(self):
    class M(Model):
      __fauna_class_name__ = "test_list_model"
      number = Field()
    Class.create_for_model(self.client, M)

    idx = ClassIndex.create_for_model(self.client, M)
    self.assertEqual(ClassIndex.get_for_model(self.client, M), idx)
    ms = [M.create(self.client, number=i) for i in range(10)]

    ms_set = idx.match()
    page = M.page(self.client, ms_set, page_size=2)
    self.assertEqual(page.data, [ms[0], ms[1]])
    page2 = M.page(self.client, ms_set, page_size=2, after=page.after)
    self.assertEqual(page2.data, [ms[2], ms[3]])

    # List of all Ms should be exactly 100 in length; use izip_longest to be sure.
    for i, m in izip_longest(range(10), M.iterator(self.client, ms_set, page_size=2)):
      self.assertEqual(m.number, i)
