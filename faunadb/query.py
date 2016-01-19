"""
Constructors for creating queries to be passed into Client.query.
For query documentation see the `docs <https://faunadb.com/documentation/queries>`_.

When constructing queries, you must use these functions or
the :any:`Ref`, :any:`Set`, :any:`FaunaTime`, and :class:`datetime.date` constructors.
"""

# pylint: disable=invalid-name, redefined-builtin

from contextlib import contextmanager
from threading import local
from types import FunctionType
from builtins import range
_thread_local = local()

#region Basic forms

def let(vars, in_expr):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  # vars is a dict, but we don't want it converted to an object expression.
  vars_expr = _Expr(_convert_values(vars))
  return _q({"let": vars_expr, "in": in_expr})


def var(var_name):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return _q({"var": var_name})


def if_expr(condition, then, else_):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return _q({"if": condition, "then": then, "else": else_})


def do(*expressions):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return _q({"do": _varargs(expressions)})


def lambda_query(func):
  """
  See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__.
  This form generates the names of lambda parameters for you, and is called like::

      query.lambda_query(lambda a: query.add(a, a))
      # Produces: {
      #  "lambda": "auto0",
      #  "expr": {"add": ({"var": "auto0"}, {"var": "auto0"})}
      # }

  You usually don't need to call this directly as lambdas in queries will be converted for you.
  For example: ``query.map(lambda a: query.add(a, 1), collection)``.

  You can also use :any:`lambda_expr` directly.

  :param func:
    Takes one or more :any:`var` expressions and uses them to construct an expression.
    If this has more than one argument, the lambda destructures an array argument.
    (To destructure single-element arrays use :any:`lambda_expr`.)
  """

  n_args = func.__code__.co_argcount
  if n_args == 0:
    raise ValueError("Function must take at least 1 argument.")

  with _auto_vars(n_args) as vars:
    if n_args == 1:
      return lambda_expr(vars[0], func(var(vars[0])))
    else:
      return lambda_expr(vars, func(*[var(v) for v in vars]))


def lambda_expr(var_name_or_pattern, expr):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return _q({"lambda": var_name_or_pattern, "expr": expr})

#endregion

#region Collection functions

def map_expr(lambda_expr, collection):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  # pylint: disable=redefined-outer-name
  return _q({"map": lambda_expr, "collection": collection})


def foreach(lambda_expr, collection):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  # pylint: disable=redefined-outer-name
  return _q({"foreach": lambda_expr, "collection": collection})


def filter_expr(lambda_expr, collection):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  # pylint: disable=redefined-outer-name
  return _q({"filter": lambda_expr, "collection": collection})


def take(number, collection):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  return _q({"take": number, "collection": collection})


def drop(number, collection):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  return _q({"drop": number, "collection": collection})


def prepend(elements, collection):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  return _q({"prepend": elements, "collection": collection})


def append(elements, collection):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  return _q({"append": elements, "collection": collection})

#endregion

#region Read functions

def get(ref, ts=None):
  """See the `docs <https://faunadb.com/documentation/queries#read_functions>`__."""
  return _params({"get": ref}, {"ts": ts})


def paginate(
    set, size=None, ts=None, after=None, before=None, events=None, sources=None):
  """
  See the `docs <https://faunadb.com/documentation/queries#read_functions>`__.
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
  """See the `docs <https://faunadb.com/documentation/queries#read_functions>`__."""
  return _params({"exists": ref}, {"ts": ts})


def count(set, events=None):
  """See the `docs <https://faunadb.com/documentation/queries#read_functions>`__."""
  return _params({"count": set}, {"events": events})

#endregion

#region Write functions

def create(class_ref, params):
  """See the `docs <https://faunadb.com/documentation/queries#write_functions>`__."""
  return _q({"create": class_ref, "params": params})


def update(ref, params):
  """See the `docs <https://faunadb.com/documentation/queries#write_functions>`__."""
  return _q({"update": ref, "params": params})


def replace(ref, params):
  """See the `docs <https://faunadb.com/documentation/queries#write_functions>`__."""
  return _q({"replace": ref, "params": params})


def delete(ref):
  """See the `docs <https://faunadb.com/documentation/queries#write_functions>`__."""
  return _q({"delete": ref})


def insert(ref, ts, action, params):
  """See the `docs <https://faunadb.com/documentation/queries#write_functions>`__."""
  return _q({"insert": ref, "ts": ts, "action": action, "params": params})


def remove(ref, ts, action):
  """See the `docs <https://faunadb.com/documentation/queries#write_functions>`__."""
  return _q({"remove": ref, "ts": ts, "action": action})

#endregion

#region Sets

def match(index, *terms):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return _q({"match": index, "terms": _varargs(terms)})


def union(*sets):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return _q({"union": _varargs(sets)})


def intersection(*sets):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return _q({"intersection": _varargs(sets)})


def difference(*sets):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return _q({"difference": _varargs(sets)})


def join(source, target):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return _q({"join": source, "with": target})

#endregion

#region Authentication

def login(ref, params):
  """See the `docs <https://faunadb.com/documentation/queries#auth_functions>`__."""
  return _q({"login": ref, "params": params})


def logout(delete_tokens):
  """See the `docs <https://faunadb.com/documentation/queries#auth_functions>`__."""
  return _q({"logout": delete_tokens})


def identify(ref, password):
  """See the `docs <https://faunadb.com/documentation/queries#auth_functions>`__."""
  return _q({"identify": ref, "password": password})

#endregion

#region String functions

def concat(strings, separator=None):
  """See the `docs <https://faunadb.com/documentation/queries#string_functions>`__."""
  return _params({"concat": strings}, {"separator": separator})


def casefold(string):
  """See the `docs <https://faunadb.com/documentation/queries#string_functions>`__."""
  return _q({"casefold": string})

#endregion

#region Time and date functions

def time(string):
  """See the `docs <https://faunadb.com/documentation/queries#time_functions>`__."""
  return _q({"time": string})


def epoch(number, unit):
  """See the `docs <https://faunadb.com/documentation/queries#time_functions>`__."""
  return _q({"epoch": number, "unit": unit})


def date(string):
  """See the `docs <https://faunadb.com/documentation/queries#time_functions>`__."""
  return _q({"date": string})

#endregion

#region Miscellaneous functions

def equals(*values):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"equals": _varargs(values)})


def contains(path, in_):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"contains": path, "in": in_})


def select(path, from_):
  """
  See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__.
  See also :py:func:`select_with_default`."""
  return _q({"select": path, "from": from_})


def select_with_default(path, from_, default):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"select": path, "from": from_, "default": default})


def add(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"add": _varargs(numbers)})


def multiply(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"multiply": _varargs(numbers)})


def subtract(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"subtract": _varargs(numbers)})


def divide(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"divide": _varargs(numbers)})


def modulo(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"modulo": _varargs(numbers)})


def lt(*values):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"lt": _varargs(values)})


def lte(*values):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"lte": _varargs(values)})


def gt(*values):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"gt": _varargs(values)})


def gte(*values):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"gte": _varargs(values)})


def and_expr(*booleans):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"and": _varargs(booleans)})


def or_expr(*booleans):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"or": _varargs(booleans)})


def not_expr(boolean):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _q({"not": boolean})

#endregion

#region Helpers

class _Expr(object):
  """
  Used to mark values that have been converted to queries.
  :any:`to_query` simply unwraps these.
  """

  def __init__(self, value):
    self.value = value


def to_query(value):
  """
  Converts any value to a query, recursively.
  Lambdas are converted using :any:`lambda_query`.
  Dicts are converted to `object queries <https://faunadb.com/documentation/queries#basic_forms>`__.
  """
  if isinstance(value, _Expr):
    return value.value
  elif isinstance(value, FunctionType):
    return lambda_query(value).value
  elif isinstance(value, dict):
    return {"object": _convert_values(value)}
  elif isinstance(value, list) or isinstance(value, tuple):
    return [to_query(sub_value) for sub_value in value]
  else:
    return value


def _q(dct):
  """
  Make a query.
  Arguments should be converted.
  The result is wrapped in _Expr so it doesn't get converted itself.
  """
  return _Expr(_convert_values(dct))


def _convert_values(dct):
  return {key: to_query(val) for key, val in dct.items()}


@contextmanager
def _auto_vars(n_vars):
  if not hasattr(_thread_local, "fauna_lambda_var_number"):
    _thread_local.fauna_lambda_var_number = 0

  low_var_number = _thread_local.fauna_lambda_var_number
  next_var_number = low_var_number + n_vars

  _thread_local.fauna_lambda_var_number = next_var_number

  try:
    yield ["auto%i" % i for i in range(low_var_number, next_var_number)]
  finally:
    _thread_local.fauna_lambda_var_number = low_var_number


def _params(main_params, optional_params):
  """Hash of query arguments with None values removed."""
  for key, val in optional_params.items():
    if val is not None:
      main_params[key] = val
  return _q(main_params)


def _varargs(values):
  """
  Called on ``*args`` arguments.
  This ensures that a single value passed is not put in an array, so
  ``query.add([1, 2])`` will work as well as ``query.add(1, 2)``.
  """
  return values[0] if len(values) == 1 else values

#endregion
