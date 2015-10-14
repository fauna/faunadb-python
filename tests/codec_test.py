from faunadb.errors import InvalidValue
from faunadb.objects import Ref
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

      def encode(self, value):
        return value + value

      def decode(self, raw):
        half = len(raw) / 2
        assert raw[:half] == raw[half:]
        return raw[:half]

    class MyModel(Model):
      __fauna_class_name__ = "my_models"
      plain_field = Field()
      codec_field = Field(codec=DoubleCodec())
    MyModel.ref_field = Field(RefCodec)
    self.MyModel = MyModel
    Class.create_for_model(self.client, MyModel)

    self.instance = MyModel(self.client, plain_field=1, codec_field="doubleme")

  def test_model_fields(self):
    pf = Field()
    class MyModel(Model):
      __fauna_class_name__ = "my_models"
      plain_field = pf
    rf = Field(RefCodec)
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
    assert it.codec_field == "doub"
    assert it.get_encoded("codec_field") == "doubdoub"

  def test_ref_codec(self):
    it = self.MyModel(self.client)
    assert it.ref_field is None

    ref = Ref('frogs', 123)
    it.ref_field = 'frogs/123'
    assert it.ref_field == ref

    it.ref_field = ref
    assert it.ref_field == ref

    # Fails for any other input
    def setBadValue():
      it.ref_field = 123
    self.assertRaises(InvalidValue, setBadValue)
