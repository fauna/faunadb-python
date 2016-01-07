from ..objects import Ref
from .. import query
from .codec import RefCodec
from .field import Field
from .model import Model, _ModelMetaClass


class _BuiltinMetaClass(_ModelMetaClass):
  def __init__(cls, name, bases, dct):
    super(_BuiltinMetaClass, cls).__init__(name, bases, dct)
    if not cls.is_abstract():
      # class_ref does not have 'classes' in front
      cls.class_ref = Ref(cls.__fauna_class_name__)
      for field_name in cls.fields:
        # Builtin fields do not have "data" in front of path
        cls.fields[field_name].path = [field_name]


class Builtin(Model):
  """
  Builtins are special classes that exist by default.

  If you want to store custom data, you can add new fields to these builtins.
  """

  __metaclass__ = _BuiltinMetaClass


class Database(Builtin):
  """See the `docs <https://faunadb.com/documentation/objects#databases>`__."""

  __fauna_class_name__ = "databases"
  name = Field()
  api_version = Field()


class Key(Builtin):
  """See the `docs <https://faunadb.com/documentation/objects#keys>`__."""

  __fauna_class_name__ = "keys"
  database = Field(RefCodec)
  role = Field()
  secret = Field()
  hashed_secret = Field()


class Class(Builtin):
  """
  See the `docs <https://faunadb.com/documentation/objects#classes>`__.
  This is faunadb's representation of a :any:`Model` class.
  """

  __fauna_class_name__ = "classes"
  name = Field()
  history_days = Field()
  ttl_days = Field()
  permissions = Field()

  @staticmethod
  def create_for_model(client, model_class, **kwargs):
    """Creates a class for the :any:`Model`."""
    return Class.create(client, name=model_class.__fauna_class_name__, **kwargs)

  @staticmethod
  def get_for_model(client, model_class):
    """Gets the class associated with a :any:`Model`."""
    return Class.get(client, model_class.class_ref)


class Index(Builtin):
  """See the `docs <https://faunadb.com/documentation/objects#indexes>`__."""

  __fauna_class_name__ = "indexes"
  name = Field()
  source = Field(RefCodec)
  terms = Field()
  values = Field()
  unique = Field()
  permissions = Field()
  active = Field()

  @staticmethod
  def create_for_model(client, model_class, name, terms, **kwargs):
    """
    Creates an Index for a :any:`Model` class.
    The index may not be usable immediately. See the docs.

    :param terms:
      If a str, transformed to ``[{"path": "data.xxx"}]`` where :samp:`xxx` is the provided str.
      Otherwise, an array looking like ``[{"path": ...}, {"path": ...}, ...]``.
    """

    if isinstance(terms, str):
      terms = [{"path": "data.%s" % terms}]

    source = Class.get_for_model(client, model_class)
    return Index.create(client, source=source.ref, name=name, terms=terms, **kwargs)

  def match(self, *matched_values):
    """
    Set query representing all instances whose value matches the index's term.
    See also :any:`Model.page_index` and :any:`Model.iter_index`.

    :param matched_values:
      For each term in :samp:`self.terms`, a value that must be matched.
    """
    # Make query slightly neater by only using an array if necessary.
    if len(matched_values) == 1:
      matched_values = matched_values[0]
    return query.match(matched_values, self.ref)

  def get_single(self, *matched_values):
    """
    Returns raw data of the first instance matched by this index.
    Typically this will be used for an index with :samp:`unique = True`.
    See also :any:`Model.get_from_index`.

    :param matched_values: Same as for :any:`match`.
    :return: Raw data for an instance.
    """
    return self.client.query(query.get(self.match(*matched_values)))


class ClassIndex(Index):
  """
  Index over all instances of a class.
  Not a different faunadb class; just a specialized Index.
  """

  @staticmethod
  def create_for_model(client, model_class, **kwargs):
    """
    Creates a class index for the given model.
    If the model is :samp:`classes/xyz`, the class index will be :samp:`indexes/xyz`.
    """
    #pylint: disable=arguments-differ

    name = model_class.__fauna_class_name__
    source = Class.get_for_model(client, model_class)
    terms = [{"path": "class"}]
    return ClassIndex.create(client, source=source.ref, name=name, terms=terms, **kwargs)

  @staticmethod
  def get_for_model(client, model_class):
    """
    Fetches the class index.
    :any:`create_for_model` should have been called for this database.
    """
    return ClassIndex.get_by_id(client, model_class.__fauna_class_name__)

  def match(self):
    """Query set of all instances of the class."""
    # pylint: disable=arguments-differ
    return query.match(self.get_encoded("source"), self.ref)
