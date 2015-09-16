from faunadb.errors import InvalidValue
from faunadb.model.builtin import Class
from faunadb.model.codec import Codec, RefCodec
from faunadb.model.field import Field
from faunadb.model.model import Model

from test_case import FaunaTestCase

class CodecTest(FaunaTestCase):
  def setUp(self):
    super(CodecTest, self).setUp()

    class DoubleCodec(Codec):
      # pylint: disable=no-self-use

      def encode(self, value, model):
        return value + value

      def decode(self, raw, model):
        half = len(raw) / 2
        assert raw[:half] == raw[half:]
        return raw[:half]

    class MyModel(Model):
      __fauna_class_name__ = "my_models"
      plain_field = Field()
      codec_field = Field(codec=DoubleCodec())
    MyModel.ref_field = Field(RefCodec(MyModel))
    self.MyModel = MyModel
    Class.create_for_model(self.client, MyModel)

    self.instance = MyModel(self.client, plain_field=1, codec_field="doubleme")

  def test_model_fields(self):
    pf = Field()
    class MyModel(Model):
      __fauna_class_name__ = "my_models"
      plain_field = pf
    rf = Field(RefCodec(MyModel))
    MyModel.ref_field = rf

    assert set(MyModel.fields.iterkeys()) == {"plain_field", "ref_field"}
    assert MyModel.fields["plain_field"] is pf
    assert MyModel.fields["ref_field"] is rf

  def test_no_codec(self):
    assert self.instance.plain_field == 1
    self.instance.plain_field = 2
    assert self.instance.plain_field == 2

  def test_custom_codec(self):
    it = self.instance
    assert it.codec_field == "doubleme"
    assert it.get_encoded("codec_field") == "doublemedoubleme"
    it.codec_field = "doub"
    assert it.get_encoded("codec_field") == "doubdoub"
    assert it.codec_field == "doub"

  def test_ref_codec(self):
    it = self.instance

    other = self.MyModel(self.client, plain_field=2, codec_field="ddd", ref_field=None)
    assert it.ref_field == None

    def set_field():
      it.ref_field = other
    # Fails because 'other' has no Ref yet.
    self.assertRaises(InvalidValue, set_field)
    other.save()
    set_field()
    assert it.get_encoded("ref_field") == other.ref
    assert it.ref_field == other

    it.save()
    it.ref_field = it

    assert it.get_encoded("ref_field") == it.ref
    assert it.ref_field == it

    it.save()
    assert self.MyModel.get(self.client, it.ref).ref_field.ref == it.ref

    # Values of wrong type will not save
    class MyOtherModel(Model):
      __fauna_class_name__ = "my_other_models"
    Class.create_for_model(self.client, MyOtherModel)

    other_model = MyOtherModel.create(self.client)
    def set_to_other():
      it.ref_field = other_model
    self.assertRaises(InvalidValue, set_to_other)
