"""
This module contains functions that generate query objects,
suitable to be passed into :any:`FaunaClient.query`.

In addition to these functions, queries may contain:

* ``None``
* Numbers (``1, 2.5``)
* Strings (``"foo"``)
* Lists (``[1, "foo"]``)
* Dicts (``{"foo": "bar"}``)
* A :any:`Ref`, :any:`SetRef`, :any:`FaunaTime`, or :class:`datetime.date`.

For example: ``select("a", {"a": Ref("123", Ref("widgets", Native.CLASSES))})``.
"""

# pylint: disable=invalid-name, redefined-builtin

from types import FunctionType
from faunadb.deprecated import deprecated

#region Basic forms

def abort(msg):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"abort": msg})

def ref(collection_ref, id=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  if id is None:
    return _fn({"@ref": collection_ref})
  return _fn({"ref": collection_ref, "id": id})


@deprecated("use collections instead")
def classes(scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"classes": scope})

def collections(scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"collections": scope})

def databases(scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"databases": scope})

def indexes(scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"indexes": scope})

def functions(scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"functions": scope})

def roles(scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"roles": scope})

def keys(scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"keys": scope})

def tokens(scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"tokens": scope})

def credentials(scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"credentials": scope})

def at(timestamp, expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"at": timestamp, "expr": expr})

class LetBindings:
  def __init__(self, bindings):
    self._bindings = bindings
  def in_(self, in_expr):
    return _fn({"let": self._bindings, "in": in_expr})


def let(*args, **kwargs):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  if kwargs:
    return LetBindings([_fn({k: v}) for k, v in kwargs.items()])
  else:
    bindings = [_fn({k: v}) for k, v in args[0].items()]
    in_expr = args[1]
    return _fn({"let": bindings, "in": in_expr})


def var(var_name):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"var": var_name})


@deprecated("use if_ instead")
def if_expr(condition, then, else_):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return if_(condition, then, else_)


def if_(condition, then, else_):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"if": condition, "then": then, "else": else_})


def do(*expressions):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"do": expressions})


def lambda_query(func):
  """
  See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__.
  This form generates :any:`var` objects for you, and is called like::

      query.lambda_query(lambda a: query.add(a, a))
      # Produces: {
      #  "lambda": "a",
      #  "expr": {"add": ({"var": "a"}, {"var": "a"})}
      # }

  You usually don't need to call this directly as lambdas in queries will be converted for you.
  For example: ``query.map_(lambda a: query.add(a, 1), collection)``.

  You can also use :any:`lambda_` directly.

  :param func:
    Takes one or more :any:`var` expressions and uses them to construct an expression.
    If this has more than one argument, the lambda destructures an array argument.
    (To destructure single-element arrays use :any:`lambda_`.)
  """

  vars = func.__code__.co_varnames
  n_args = len(vars)

  if n_args == 0:
    raise ValueError("Function must take at least 1 argument.")
  elif n_args == 1:
    v = vars[0]
    return lambda_(v, func(var(v)))
  else:
    return lambda_(vars, func(*[var(v) for v in vars]))


@deprecated("use lambda_ instead")
def lambda_expr(var_name_or_pattern, expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return lambda_(var_name_or_pattern, expr)


def lambda_(var_name_or_pattern, expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"lambda": var_name_or_pattern, "expr": expr})


def call(ref_, *arguments):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  return _fn({"call": ref_, "arguments": _varargs(arguments)})


def query(_lambda):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#basic-forms>`__."""
  if isinstance(_lambda, FunctionType):
    _lambda = lambda_query(_lambda)
  return _fn({"query": _lambda})

#endregion

#region Collection functions

@deprecated("use map_ instead")
def map_expr(expr, collection):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return map_(expr, collection)


def map_(expr, collection):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#collections>`__."""
  return _fn({"map": expr, "collection": collection})


def foreach(expr, collection):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#collections>`__."""
  return _fn({"foreach": expr, "collection": collection})


@deprecated("use filter_ instead")
def filter_expr(expr, collection):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return filter_(expr, collection)


def filter_(expr, collection):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#collections>`__."""
  return _fn({"filter": expr, "collection": collection})


def take(number, collection):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#collections>`__."""
  return _fn({"take": number, "collection": collection})


def drop(number, collection):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#collections>`__."""
  return _fn({"drop": number, "collection": collection})


def prepend(elements, collection):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#collections>`__."""
  return _fn({"prepend": elements, "collection": collection})


def append(elements, collection):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#collections>`__."""
  return _fn({"append": elements, "collection": collection})

def is_empty(collection):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#collections>`__."""
  return _fn({"is_empty": collection})

def is_nonempty(collection):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#collections>`__."""
  return _fn({"is_nonempty": collection})

#endregion

#region Read functions

def get(ref_, ts=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#read-functions>`__."""
  return _params({"get": ref_}, {"ts": ts})


def key_from_secret(secret):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#read-functions>`__."""
  return _fn({"key_from_secret": secret})


def paginate(
    set, size=None, ts=None, after=None, before=None, events=None, sources=None):
  """
  See the `docs <https://app.fauna.com/documentation/reference/queryapi#read-functions>`__.
  You may want to convert the result of this to a :any:`Page`.
  """
  # pylint: disable=too-many-arguments
  # pylint: disable=redefined-outer-name
  opts = {
    "size": size,
    "ts": ts,
    "after": after,
    "before": before,
    "events": events,
    "sources": sources
  }
  return _params({"paginate": set}, opts)


def exists(ref_, ts=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#read-functions>`__."""
  return _params({"exists": ref_}, {"ts": ts})

#endregion

#region Write functions

def create(collection_ref, params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"create": collection_ref, "params": params})


def update(ref_, params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"update": ref_, "params": params})


def replace(ref_, params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"replace": ref_, "params": params})


def delete(ref_):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"delete": ref_})


def insert(ref_, ts, action, params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"insert": ref_, "ts": ts, "action": action, "params": params})


def remove(ref_, ts, action):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"remove": ref_, "ts": ts, "action": action})

@deprecated("use create_collection instead")
def create_class(class_params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"create_class": class_params})

def create_collection(collection_params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"create_collection": collection_params})

def create_database(db_params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"create_database": db_params})


def create_index(index_params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"create_index": index_params})


def create_function(func_params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"create_function": func_params})


def create_role(func_params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"create_role": func_params})


def create_key(key_params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#write-functions>`__."""
  return _fn({"create_key": key_params})

#endregion

#region Sets

def singleton(ref_):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#sets>`__."""
  return _fn({"singleton": ref_})


def events(ref_set):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#sets>`__."""
  return _fn({"events": ref_set})


def match(index, *terms):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#sets>`__."""
  # pylint: disable=redefined-outer-name
  m = {"match": index}

  if len(terms) >= 1:
    m["terms"] = _varargs(terms)

  return _fn(m)


def union(*sets):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#sets>`__."""
  return _fn({"union": _varargs(sets)})


def intersection(*sets):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#sets>`__."""
  return _fn({"intersection": _varargs(sets)})


def difference(*sets):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#sets>`__."""
  return _fn({"difference": _varargs(sets)})


def distinct(set):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#sets>`__."""
  return _fn({"distinct": set})


def join(source, target):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#sets>`__."""
  return _fn({"join": source, "with": target})

#endregion

#region Authentication

def login(ref_, params):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#authentication>`__."""
  return _fn({"login": ref_, "params": params})


def logout(delete_tokens):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#authentication>`__."""
  return _fn({"logout": delete_tokens})


def identify(ref_, password):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#authentication>`__."""
  return _fn({"identify": ref_, "password": password})


def identity():
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#authentication>`__."""
  return _fn({"identity": None})


def has_identity():
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#authentication>`__."""
  return _fn({"has_identity": None})

#endregion

#region String functions

def concat(strings, separator=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#string-functions>`__."""
  return _params({"concat": strings}, {"separator": separator})


def casefold(string, normalizer=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#string-functions>`__."""
  return _params({"casefold": string}, {"normalizer": normalizer})


def ngram(terms, min=None, max=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#string-functions>`__."""
  return _params({"ngram": terms}, {"min": min, "max": max})


def find_str(value, find, start=None):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _params({"findstr": value, "find": find}, {"start": start})


def find_str_regex(value, pattern, start=None, numResults=None):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _params({"findstrregex": value, "pattern": pattern}, {"start": start, "num_results": numResults})


def replace_str(value, find, replace):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _fn({"replacestr": value, "find": find, "replace": replace})


def replace_str_regex(value, pattern, replace, first=None):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _params({"replacestrregex": value, "pattern": pattern, "replace": replace}, {"first": first})


def length(value):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _fn({"length": value})


def lowercase(value):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _fn({"lowercase": value})


def uppercase(value):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _fn({"uppercase": value})


def titlecase(value):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _fn({"titlecase": value})


def trim(value):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _fn({"trim": value})


def ltrim(value):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _fn({"ltrim": value})


def rtrim(value):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _fn({"rtrim": value})


def space(count):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _fn({"space": count})


def substring(value, start, length=None):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _params({"substring": value, "start": start}, {"length": length})


def repeat(value, number=None):
  """See the docs <https://app.fauna.com/documentation/reference/queryapi#string-functions> __."""
  return _params({"repeat": value}, {"number": number})

#endregion

#region Time and date functions

def time(string):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"time": string})


def epoch(number, unit):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"epoch": number, "unit": unit})


def date(string):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"date": string})

#endregion

#region Miscellaneous functions

@deprecated("use new_id instead")
def next_id():
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"next_id": None})


def new_id():
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"new_id": None})


def database(db_name, scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _params({"database": db_name}, {"scope": scope})


def index(index_name, scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _params({"index": index_name}, {"scope": scope})


@deprecated("use collection instead")
def class_expr(class_name, scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return class_(class_name, scope)

@deprecated("use collection instead")
def class_(class_name, scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _params({"class": class_name}, {"scope": scope})

def collection(collection_name, scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _params({"collection": collection_name}, {"scope": scope})

def function(fn_name, scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _params({"function": fn_name}, {"scope": scope})


def role(role_name, scope=None):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _params({"role": role_name}, {"scope": scope})


def equals(*values):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"equals": _varargs(values)})


def contains(path, in_):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"contains": path, "in": in_})


def select(path, from_):
  """
  See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__.
  See also :py:func:`select_with_default`."""
  return _fn({"select": path, "from": from_})


def select_with_default(path, from_, default):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"select": path, "from": from_, "default": default})


def select_all(path, from_):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"select_all": path, "from": from_})


def add(*numbers):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"add": _varargs(numbers)})


def multiply(*numbers):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"multiply": _varargs(numbers)})


def subtract(*numbers):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"subtract": _varargs(numbers)})


def divide(*numbers):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"divide": _varargs(numbers)})


def modulo(*numbers):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"modulo": _varargs(numbers)})


def lt(*values):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"lt": _varargs(values)})


def lte(*values):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"lte": _varargs(values)})


def gt(*values):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"gt": _varargs(values)})


def gte(*values):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"gte": _varargs(values)})


@deprecated("use and_ instead")
def and_expr(*booleans):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return and_(*booleans)


def and_(*booleans):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"and": _varargs(booleans)})


@deprecated("use or_ instead")
def or_expr(*booleans):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return or_(*booleans)


def or_(*booleans):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"or": _varargs(booleans)})


@deprecated("use not_ instead")
def not_expr(boolean):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return not_(boolean)


def not_(boolean):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#miscellaneous-functions>`__."""
  return _fn({"not": boolean})

def to_string(expr):
  return _fn({"to_string": expr})

def to_number(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"to_number": expr})

def to_time(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"to_time": expr})

def to_seconds(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"to_seconds": expr})

def to_millis(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"to_millis": expr})

def to_micros(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"to_micros": expr})

def day_of_month(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"day_of_month": expr})

def day_of_week(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"day_of_week": expr})

def day_of_year(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"day_of_year": expr})

def year(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"year": expr})

def month(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"month": expr})

def hour(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"hour": expr})

def minute(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"minute": expr})

def second(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"second": expr})

def to_date(expr):
  """See the `docs <https://app.fauna.com/documentation/reference/queryapi#time-and-date>`__."""
  return _fn({"to_date": expr})

#endregion

#region Helpers

class _Expr(object):
  """
  Used to mark values that have been wrapped.
  """

  def __init__(self, value):
    self.value = value

  def to_fauna_json(self):
    return self.value

  def __repr__(self):
    return "Expr(%s)" % repr(self.value)

  def __eq__(self, other):
    return isinstance(other, _Expr) and self.value == other.value


def _wrap(value):
  if isinstance(value, _Expr):
    return value
  elif isinstance(value, FunctionType):
    return lambda_query(value)
  elif isinstance(value, dict):
    return _Expr({"object": _wrap_values(value)})
  elif isinstance(value, (list, tuple)):
    return _Expr([_wrap(sub_value) for sub_value in value])
  return value


def _wrap_values(dct):
  return {key: _wrap(val) for key, val in dct.items()}


def _fn(dct):
  return _Expr(_wrap_values(dct))


def _params(main_params, optional_params):
  """Hash of query arguments with None values removed."""
  for key, val in optional_params.items():
    if val is not None:
      main_params[key] = val
  return _fn(main_params)


def _varargs(values):
  """
  Called on ``*args`` arguments.
  This ensures that a single value passed is not put in an array, so
  ``query.add([1, 2])`` will work as well as ``query.add(1, 2)``.
  """
  return values[0] if len(values) == 1 else values

#endregion
