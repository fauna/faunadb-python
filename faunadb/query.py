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

For example: ``select("a", {"a": Ref("widgets", 123)})``.
"""

# pylint: disable=invalid-name, redefined-builtin

from types import FunctionType

#region Basic forms

def let(vars, in_expr):
  """See the `docs <https://fauna.com/documentation/queries#basic_forms>`__."""
  return _fn({"let": _fn(vars), "in": in_expr})


def var(var_name):
  """See the `docs <https://fauna.com/documentation/queries#basic_forms>`__."""
  return _fn({"var": var_name})


def if_expr(condition, then, else_):
  """See the `docs <https://fauna.com/documentation/queries#basic_forms>`__."""
  return _fn({"if": condition, "then": then, "else": else_})


def do(*expressions):
  """See the `docs <https://fauna.com/documentation/queries#basic_forms>`__."""
  return _fn({"do": _varargs(expressions)})


def lambda_query(func):
  """
  See the `docs <https://fauna.com/documentation/queries#basic_forms>`__.
  This form generates :any:`var` objects for you, and is called like::

      query.lambda_query(lambda a: query.add(a, a))
      # Produces: {
      #  "lambda": "a",
      #  "expr": {"add": ({"var": "a"}, {"var": "a"})}
      # }

  You usually don't need to call this directly as lambdas in queries will be converted for you.
  For example: ``query.map_expr(lambda a: query.add(a, 1), collection)``.

  You can also use :any:`lambda_expr` directly.

  :param func:
    Takes one or more :any:`var` expressions and uses them to construct an expression.
    If this has more than one argument, the lambda destructures an array argument.
    (To destructure single-element arrays use :any:`lambda_expr`.)
  """

  vars = func.__code__.co_varnames
  n_args = len(vars)

  if n_args == 0:
    raise ValueError("Function must take at least 1 argument.")
  elif n_args == 1:
    v = vars[0]
    return lambda_expr(v, func(var(v)))
  else:
    return lambda_expr(vars, func(*[var(v) for v in vars]))


def lambda_expr(var_name_or_pattern, expr):
  """See the `docs <https://fauna.com/documentation/queries#basic_forms>`__."""
  return _fn({"lambda": var_name_or_pattern, "expr": expr})

#endregion

#region Collection functions

def map_expr(expr, collection):
  """See the `docs <https://fauna.com/documentation/queries#collection_functions>`__."""
  return _fn({"map": expr, "collection": collection})


def foreach(expr, collection):
  """See the `docs <https://fauna.com/documentation/queries#collection_functions>`__."""
  return _fn({"foreach": expr, "collection": collection})


def filter_expr(expr, collection):
  """See the `docs <https://fauna.com/documentation/queries#collection_functions>`__."""
  return _fn({"filter": expr, "collection": collection})


def take(number, collection):
  """See the `docs <https://fauna.com/documentation/queries#collection_functions>`__."""
  return _fn({"take": number, "collection": collection})


def drop(number, collection):
  """See the `docs <https://fauna.com/documentation/queries#collection_functions>`__."""
  return _fn({"drop": number, "collection": collection})


def prepend(elements, collection):
  """See the `docs <https://fauna.com/documentation/queries#collection_functions>`__."""
  return _fn({"prepend": elements, "collection": collection})


def append(elements, collection):
  """See the `docs <https://fauna.com/documentation/queries#collection_functions>`__."""
  return _fn({"append": elements, "collection": collection})

#endregion

#region Read functions

def get(ref, ts=None):
  """See the `docs <https://fauna.com/documentation/queries#read_functions>`__."""
  return _params({"get": ref}, {"ts": ts})


def paginate(
    set, size=None, ts=None, after=None, before=None, events=None, sources=None):
  """
  See the `docs <https://fauna.com/documentation/queries#read_functions>`__.
  You may want to convert the result of this to a :any:`Page`.
  """
  # pylint: disable=too-many-arguments
  opts = {
    "size": size,
    "ts": ts,
    "after": after,
    "before": before,
    "events": events,
    "sources": sources
  }
  return _params({"paginate": set}, opts)


def exists(ref, ts=None):
  """See the `docs <https://fauna.com/documentation/queries#read_functions>`__."""
  return _params({"exists": ref}, {"ts": ts})

#endregion

#region Write functions

def create(class_ref, params):
  """See the `docs <https://fauna.com/documentation/queries#write_functions>`__."""
  return _fn({"create": class_ref, "params": params})


def update(ref, params):
  """See the `docs <https://fauna.com/documentation/queries#write_functions>`__."""
  return _fn({"update": ref, "params": params})


def replace(ref, params):
  """See the `docs <https://fauna.com/documentation/queries#write_functions>`__."""
  return _fn({"replace": ref, "params": params})


def delete(ref):
  """See the `docs <https://fauna.com/documentation/queries#write_functions>`__."""
  return _fn({"delete": ref})


def insert(ref, ts, action, params):
  """See the `docs <https://fauna.com/documentation/queries#write_functions>`__."""
  return _fn({"insert": ref, "ts": ts, "action": action, "params": params})


def remove(ref, ts, action):
  """See the `docs <https://fauna.com/documentation/queries#write_functions>`__."""
  return _fn({"remove": ref, "ts": ts, "action": action})


def create_class(class_params):
  """See the `docs <https://fauna.com/documentation/queries#write_functions>`__."""
  return _fn({"create_class": class_params})


def create_database(db_params):
  """See the `docs <https://fauna.com/documentation/queries#write_functions>`__."""
  return _fn({"create_database": db_params})


def create_index(index_params):
  """See the `docs <https://fauna.com/documentation/queries#write_functions>`__."""
  return _fn({"create_index": index_params})


def create_key(key_params):
  """See the `docs <https://fauna.com/documentation/queries#write_functions>`__."""
  return _fn({"create_key": key_params})

#endregion

#region Sets

def match(index, *terms):
  """See the `docs <https://fauna.com/documentation/queries#sets>`__."""
  # pylint: disable=redefined-outer-name
  m = {"match": index}

  if len(terms) >= 1:
    m["terms"] = _varargs(terms)

  return _fn(m)


def union(*sets):
  """See the `docs <https://fauna.com/documentation/queries#sets>`__."""
  return _fn({"union": _varargs(sets)})


def intersection(*sets):
  """See the `docs <https://fauna.com/documentation/queries#sets>`__."""
  return _fn({"intersection": _varargs(sets)})


def difference(*sets):
  """See the `docs <https://fauna.com/documentation/queries#sets>`__."""
  return _fn({"difference": _varargs(sets)})


def distinct(set):
  """See the `docs <https://fauna.com/documentation/queries#sets>`__."""
  return _fn({"distinct": set})


def join(source, target):
  """See the `docs <https://fauna.com/documentation/queries#sets>`__."""
  return _fn({"join": source, "with": target})

#endregion

#region Authentication

def login(ref, params):
  """See the `docs <https://fauna.com/documentation/queries#auth_functions>`__."""
  return _fn({"login": ref, "params": params})


def logout(delete_tokens):
  """See the `docs <https://fauna.com/documentation/queries#auth_functions>`__."""
  return _fn({"logout": delete_tokens})


def identify(ref, password):
  """See the `docs <https://fauna.com/documentation/queries#auth_functions>`__."""
  return _fn({"identify": ref, "password": password})

#endregion

#region String functions

def concat(strings, separator=None):
  """See the `docs <https://fauna.com/documentation/queries#string_functions>`__."""
  return _params({"concat": strings}, {"separator": separator})


def casefold(string):
  """See the `docs <https://fauna.com/documentation/queries#string_functions>`__."""
  return _fn({"casefold": string})

#endregion

#region Time and date functions

def time(string):
  """See the `docs <https://fauna.com/documentation/queries#time_functions>`__."""
  return _fn({"time": string})


def epoch(number, unit):
  """See the `docs <https://fauna.com/documentation/queries#time_functions>`__."""
  return _fn({"epoch": number, "unit": unit})


def date(string):
  """See the `docs <https://fauna.com/documentation/queries#time_functions>`__."""
  return _fn({"date": string})

#endregion

#region Miscellaneous functions

def next_id():
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"next_id": None})


def database(db_name):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"database": db_name})


def index(index_name):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"index": index_name})


def class_expr(class_name):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"class": class_name})


def equals(*values):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"equals": _varargs(values)})


def contains(path, in_):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"contains": path, "in": in_})


def select(path, from_):
  """
  See the `docs <https://fauna.com/documentation/queries#misc_functions>`__.
  See also :py:func:`select_with_default`."""
  return _fn({"select": path, "from": from_})


def select_with_default(path, from_, default):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"select": path, "from": from_, "default": default})


def add(*numbers):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"add": _varargs(numbers)})


def multiply(*numbers):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"multiply": _varargs(numbers)})


def subtract(*numbers):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"subtract": _varargs(numbers)})


def divide(*numbers):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"divide": _varargs(numbers)})


def modulo(*numbers):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"modulo": _varargs(numbers)})


def lt(*values):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"lt": _varargs(values)})


def lte(*values):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"lte": _varargs(values)})


def gt(*values):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"gt": _varargs(values)})


def gte(*values):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"gte": _varargs(values)})


def and_expr(*booleans):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"and": _varargs(booleans)})


def or_expr(*booleans):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"or": _varargs(booleans)})


def not_expr(boolean):
  """See the `docs <https://fauna.com/documentation/queries#misc_functions>`__."""
  return _fn({"not": boolean})

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
  elif isinstance(value, list) or isinstance(value, tuple):
    return _Expr([_wrap(sub_value) for sub_value in value])
  else:
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
