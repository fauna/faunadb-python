from faunadb.errors import InvalidValue
from faunadb.model.builtin import Class
from faunadb.model.converter import Converter, RefConverter
from faunadb.model.field import Field
from faunadb.model.model import Model

from test_case import FaunaTestCase

class ConverterTest(FaunaTestCase):
  def setUp(self):
    super(ConverterTest, self).setUp()

    class DoubleConverter(Converter):
      # pylint: disable=no-self-use

      def raw_to_value(self, raw, model):
        half = len(raw) / 2
        assert raw[:half] == raw[half:]
        return raw[:half]

      def value_to_raw(self, value, model):
        return value + value

    class MyModel(Model):
      __fauna_class_name__ = "my_models"
      plain_field = Field()
      converted_field = Field(converter=DoubleConverter())
    MyModel.ref_field = Field(RefConverter(MyModel, nullable=True))
    self.MyModel = MyModel
    Class.create_for_model(self.client, MyModel)

    self.instance = MyModel(self.client, plain_field=1, converted_field="doubleme")

  def test_model_fields(self):
    pf = Field()
    class MyModel(Model):
      __fauna_class_name__ = "my_models"
      plain_field = pf
    rf = Field(RefConverter(MyModel))
    MyModel.ref_field = rf

    assert set(MyModel.fields.iterkeys()) == {"plain_field", "ref_field"}
    assert MyModel.fields["plain_field"] is pf
    assert MyModel.fields["ref_field"] is rf

  def test_no_conversion(self):
    assert self.instance.plain_field == 1
    self.instance.plain_field = 2
    assert self.instance.plain_field == 2

  def test_custom_conversion(self):
    it = self.instance
    assert it.converted_field == "doubleme"
    assert it.get_raw("converted_field") == "doublemedoubleme"
    it.converted_field = "doub"
    assert it.get_raw("converted_field") == "doubdoub"
    assert it.converted_field == "doub"

  def test_ref_conversion(self):
    it = self.instance

    other = self.MyModel(self.client, plain_field=2, converted_field="ddd", ref_field=None)
    assert it.ref_field == None

    def set_field():
      it.ref_field = other
    self.assertRaises(InvalidValue, set_field)
    other.save()
    set_field()
    assert it.get_raw("ref_field") == other.ref
    assert it.ref_field == other

    it.save()
    it.ref_field = it

    assert it.get_raw("ref_field") == it.ref
    assert it.ref_field == it

    it.save()
    assert self.MyModel.get(self.client, it.ref).ref_field.ref == it.ref
