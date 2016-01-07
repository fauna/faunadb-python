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

  def test_persistence(self):
    it = self.MyModel(self.client, number=1, letter="a")

    def get():
      return self.MyModel.get(self.client, it.ref)

    assert it.is_new_instance()

    it.save()
    assert not it.is_new_instance()
    assert get() == it

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

    it.save()
    assert it.ref is not None and it.ts is not None
    assert it.id == it.ref.id()
    ref1 = it.ref
    ts1 = it.ts

    it.number = 2
    it.save()
    assert it.ref == ref1
    assert it.ts is not None and it.ts != ts1

  def test_update(self):
    it = self.MyModel(self.client, number={"a": {"b": 1, "c": 2}})
    it.save()

    it.number["a"]["b"] = -1
    it.number["a"]["d"] = {"e": 3}
    assert it._diff() == {"data": {"number": {"a": {"b": -1, "d": {"e": 3}}}}}

    it.save()
    assert self.MyModel.get(self.client, it.ref) == it
