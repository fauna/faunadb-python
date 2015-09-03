from faunadb.errors import InvalidQuery, InvalidValue
from faunadb.model import Field, Model
from faunadb.model.builtin import Class

from test_case import FaunaTestCase

class ModelTest(FaunaTestCase):
  def setUp(self):
    super(ModelTest, self).setUp()

    class MyModel(Model):
      __fauna_class_name__ = "my_models"
      number = Field()
      letter = Field()
    Class.create_for_model(self.client, MyModel)
    self.MyModel = MyModel

  def test_persistence(self):
    it = self.MyModel(self.client, number=1, letter="a")

    def get():
      return self.MyModel.get(self.client, it.ref)

    assert it.is_new_instance()

    it.save()
    assert not it.is_new_instance()
    assert get() == it

    it.number = 2
    assert it._changed_fields == {"number"}
    it.save()
    assert it._changed_fields == set()
    assert get() == it

    it.delete()

    self.assertRaises(InvalidQuery, it.delete)

  def test_bad_field(self):
    self.assertRaises(InvalidValue, lambda: self.MyModel(self.client, nubber=1))

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
    g.save()

    assert g.number == 1
    assert g.letter == "a"
    assert GrowModel.get(self.client, g.ref) == g

  def test_ref_ts(self):
    it = self.MyModel(self.client, number=1, letter="a")

    assert it.ref is None and it.ts is None

    it.save()
    assert it.ref is not None and it.ts is not None
    ref1 = it.ref
    ts1 = it.ts

    it.number = 2
    it.save()
    assert it.ref is ref1
    assert it.ts is not None and it.ts != ts1
