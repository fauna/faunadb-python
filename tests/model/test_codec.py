from faunadb.objects import Ref
from faunadb.model.builtin import Class
from faunadb.model.codec import Codec, RefCodec
from faunadb.model.field import Field
from faunadb.model.model import Model

from ..helpers import FaunaTestCase

class CodecTest(FaunaTestCase):
  def setUp(self):
    super(CodecTest, self).setUp()

    outer_self = self

    class DoubleCodec(Codec):
      # pylint: disable=no-self-use

      def encode(self, value):
        return value + value

      def decode(self, raw):
        half = len(raw) / 2
        outer_self.assertEqual(raw[:half], raw[half:])
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

    self.assertEqual(set(MyModel.fields.iterkeys()), {"plain_field", "ref_field"})
    self.assertIs(MyModel.fields["plain_field"], pf)
    self.assertIs(MyModel.fields["ref_field"], rf)

  def test_no_codec(self):
    self.assertEqual(self.instance.plain_field, 1)
    self.instance.plain_field = 2
    self.assertEqual(self.instance.plain_field, 2)

  def test_custom_codec(self):
    it = self.instance
    self.assertEqual(it.codec_field, "doubleme")
    self.assertEqual(it.get_encoded("codec_field"), "doublemedoubleme")
    it.codec_field = "doub"
    self.assertEqual(it.codec_field, "doub")
    self.assertEqual(it.get_encoded("codec_field"), "doubdoub")

    # Test cache
    self.assertEqual(self.instance._cache, {"codec_field": "doub"})
    self.assertEqual(self.instance.codec_field, "doub")

  def test_ref_codec(self):
    it = self.MyModel(self.client)
    self.assertIsNone(it.ref_field)

    ref = Ref('frogs', 123)
    it.ref_field = 'frogs/123'
    self.assertEqual(it.ref_field, ref)

    it.ref_field = ref
    self.assertEqual(it.ref_field, ref)

    it.ref_field = None
    self.assertIsNone(it.ref_field)

    # Fails for any other input
    def setBadValue():
      it.ref_field = 123
    self.assertRaises(TypeError, setBadValue)
