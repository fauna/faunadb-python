from faunadb.errors import InvalidQuery, NotFound
from faunadb.model import Field, Model

from test_case import FaunaTestCase


class ModelTest(FaunaTestCase):
  def setUp(self):
    super(ModelTest, self).setUp()

    class MyModel(Model):
      __fauna_class_name__ = "my_models"
      number = Field()
      letter = Field()
    MyModel.create_class(self.client)
    self.MyModel = MyModel

  def test_persistence(self):
    it = self.MyModel(self.client, number=1, letter='a')

    def get():
      return self.MyModel.get(self.client, it.ref)

    assert it.is_new_instance()
    self.assertRaises(NotFound, get)

    it.create()
    assert not it.is_new_instance()
    assert get() == it

    it.number = 2
    it.update()
    assert get() == it

    it.patch(number=3)
    assert it.number == 3
    assert get() == it

    it.delete()

    self.assertRaises(InvalidQuery, it.update)
    self.assertRaises(InvalidQuery, lambda: it.patch(field=2))
    self.assertRaises(InvalidQuery, it.delete)

  def test_ref_ts(self):
    it = self.MyModel(self.client, number=1, letter='a')

    assert it.ref is None and it.ts is None

    it.create()
    assert it.ref is not None and it.ts is not None
    ref1 = it.ref
    ts1 = it.ts

    it.patch(number=2)
    assert it.ref is ref1
    assert it.ts is not None and it.ts != ts1
