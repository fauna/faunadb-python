from itertools import izip_longest

from faunadb.errors import InvalidQuery
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
    it = self.MyModel(self.client, number=1, letter="a")

    def get():
      return self.MyModel.get(self.client, it.ref)

    assert it.is_new_instance()

    it.save()
    assert not it.is_new_instance()
    assert get() == it

    it.number = 2
    assert it.changed_fields == {"number"}
    it.save()
    assert it.changed_fields == set()
    assert get() == it

    it.delete()

    self.assertRaises(InvalidQuery, it.delete)

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
    GrowModel.create_class(self.client)

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

  def test_list(self):
    class M(Model):
      __fauna_class_name__ = "ms"
      number = Field()
    M.create_class(self.client)
    M.create_class_index(self.client)

    ms = [M(self.client, number=i) for i in range(100)]
    for m in ms:
      m.save()

    page = M.list(self.client, {"size": 2})
    assert page["data"] == [ms[0], ms[1]]
    page2 = M.list(self.client, {"size": 2, "after": page["after"]})
    assert page2["data"] == [ms[2], ms[3]]

    # List of all Ms should be exactly 100 in length; use izip_longest to be sure.
    for i, m in izip_longest(range(100), M.list_all_iter(self.client)):
      assert m.number == i

