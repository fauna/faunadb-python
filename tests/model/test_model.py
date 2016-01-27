from faunadb.errors import NotFound
from faunadb.model.field import Field
from faunadb.model.model import Model
from faunadb.model.builtin import Class
from faunadb.objects import Ref

from ..helpers import FaunaTestCase

class ModelTest(FaunaTestCase):
  def setUp(self):
    super(ModelTest, self).setUp()

    class MyModel(Model):
      __fauna_class_name__ = "my_models"
      number = Field()
      letter = Field()

    Class.create_for_model(self.client, MyModel)
    self.MyModel = MyModel

  def test_common_fields(self):
    it = self.MyModel.create(self.client)
    assert isinstance(it.ref, Ref)
    assert isinstance(it.ts, int)
    assert it.id == it.ref.id()

  def test_forbidden_field_name(self):
    with self.assertRaises(RuntimeError):
      # pylint: disable=unused-variable
      class MyOtherModel(Model):
        __fauna_class_name__ = "my_other_models"
        ref = Field()

  def test_get_from_resource(self):
    ref = Ref("my_models", 123)
    it = self.MyModel.get_from_resource(self.client, {
      "class": Ref("classes", "my_models"),
      "ref": ref,
      "ts": 456,
      "data": {"number": 1}
    })
    assert it.ref == ref
    assert it.ts == 456
    assert it.number == 1
    self.assertRaises(
      AssertionError,
      lambda: self.MyModel.get_from_resource(self.client, {"class": Ref("classes", "wrong_class")}))

  def test_persistence(self):
    it = self.MyModel(self.client, number=1, letter="a")

    def get():
      return self.MyModel.get(self.client, it.ref)

    assert it.is_new_instance()

    # Can't replace/update/delete value that doesn't exist yet.
    self.assertRaises(ValueError, it.replace_query)
    self.assertRaises(ValueError, it.update_query)
    self.assertRaises(ValueError, it.delete_query)

    it.save()
    assert not it.is_new_instance()
    assert get() == it

    # Can't create twice.
    self.assertRaises(ValueError, it.create_query)

    it.number = 2
    assert it._diff() == {"data": {"number": 2}}
    it.save()
    assert it._diff() == {}
    assert get() == it

    it.delete()

    self.assertRaises(NotFound, it.delete)

  def test_bad_field(self):
    self.assertRaises(ValueError, lambda: self.MyModel(self.client, nubber=1))

  def test_replace(self):
    it = self.MyModel(self.client, number=1, letter="a")
    it.save()
    def get():
      return self.MyModel.get(self.client, it.ref)
    copy = get()

    copy.number = 2
    copy.save()

    it.letter = "b"
    # This will only update the "letter" property.
    it.save()

    assert get().number == 2
    assert get().letter == "b"

    copy.number = 3
    copy.save()

    it.letter = "c"
    it.save(replace=True)

    assert get() == it

  def test_replace_with_new_fields(self):
    class GrowModel(Model):
      __fauna_class_name__ = "grow_models"
      number = Field()
    Class.create_for_model(self.client, GrowModel)

    g = GrowModel(self.client, number=1)
    g.save()

    GrowModel.letter = Field()

    g = GrowModel.get(self.client, g.ref)
    g.letter = "a"
    g.save(True)

    assert g.number == 1
    assert g.letter == "a"
    assert GrowModel.get(self.client, g.ref) == g

  def test_ref_ts(self):
    it = self.MyModel(self.client, number=1, letter="a")

    self.assertRaises(ValueError, lambda: it.ref)
    self.assertRaises(ValueError, lambda: it.id)
    self.assertRaises(ValueError, lambda: it.ts)

    assert it.ref_or_none() is None
    assert it.id_or_none() is None
    assert it.ts_or_none() is None

    it.save()
    assert it.ref is not None and it.ts is not None
    assert it.ref_or_none() == it.ref
    assert it.id == it.ref.id()
    assert it.id_or_none() == it.id
    ref1 = it.ref
    ts1 = it.ts

    it.number = 2
    it.save()
    assert it.ref == ref1
    assert it.ts is not None and it.ts != ts1
    assert it.ts_or_none() == it.ts

  def test_update(self):
    it = self.MyModel(self.client, number={"a": {"b": 1, "c": 2}})
    it.save()

    it.number["a"]["b"] = -1
    it.number["a"]["d"] = {"e": 3}
    assert it._diff() == {"data": {"number": {"a": {"b": -1, "d": {"e": 3}}}}}

    it.save()
    assert self.MyModel.get(self.client, it.ref) == it

  def test_equality(self):
    it = self.MyModel(self.client, number=1)
    assert it == self.MyModel(self.client, number=1)
    assert it != self.MyModel(self.client, number=2)

  def test_repr(self):
    it = self.MyModel(self.client, number=1)
    assert repr(it) == "MyModel(ref=None, ts=None, number=1, letter=None)"
