"""
Constructors for creating queries to be passed into Client.query.
For query documentation see the `docs <https://faunadb.com/documentation/queries>`_.

When constructing queries, you must use these functions or
the :any:`Ref`, :any:`Set`, and :any:`Event` constructors.
To pass raw data to a query, use :any:`object` or :any:`quote`.
"""

# pylint: disable=invalid-name, redefined-builtin

from collections import Mapping, Sequence, namedtuple
from threading import local
from types import FunctionType
_thread_local = local()

from .errors import InvalidQuery

#region Basic forms

def let(vars, in_expr):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return {"let": vars, "in": in_expr}


def var(var_name):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return {"var": var_name}


def if_expr(condition, true_expr, false_expr):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return {"if": condition, "then": true_expr, "else": false_expr}


def do(*expressions):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return {"do": _varargs(expressions)}


def object(**keys_vals):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return {"object": keys_vals}


def quote(expr):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return {"quote": expr}


def lambda_query(func):
  """
  See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__.
  This form generates the names of lambda parameters for you, and is called like::

      query.lambda_query(lambda a: query.add(a, a))
      # Produces: {
      #  "lambda": "auto0",
      #  "expr": {"add": ({"var": "auto0"}, {"var": "auto0"})}
      # }

  Query functions requiring lambdas can be passed raw lambdas
  without explicitly calling :any:`lambda_query`.
  For example: ``query.map(lambda a: query.add(a, 1), collection)``.

  You can also use :any:`lambda_expr` directly.

  :param func: Takes a :any:`var` and uses it to construct an expression.
  """
  if not hasattr(_thread_local, "fauna_lambda_var_number"):
    _thread_local.fauna_lambda_var_number = 0

  var_name = "auto%i" % _thread_local.fauna_lambda_var_number
  _thread_local.fauna_lambda_var_number += 1

  # Make sure lambda_auto_var_number returns to its former value even if there are errors.
  try:
    return lambda_expr(var_name, func(var(var_name)))
  finally:
    _thread_local.fauna_lambda_var_number -= 1


def _to_lambda(value):
  """ If ``value`` is a lambda, converts it to a query using :any:`lambda_query`."""
  if isinstance(value, FunctionType):
    return lambda_query(value)
  else:
    return value


def lambda_pattern(pattern, func):
  """
  See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__.
  This form gathers variables from the pattern you provide and puts them in an object.
  It is called like::

      q = query.map_expr(
        query.lambda_pattern(["foo", "", "bar"], lambda args: [args.bar, args.foo]),
        [[1, 2, 3], [4, 5, 6]]))
      # Result of client.query(q) is: [[3, 1], [6, 4]].

  You can also destructure the namedtuple; in this case, variables are sorted alphabetically::

      query.lambda_pattern(["foo", "", "bar"], lambda (bar, foo): [bar, foo])

  :param Sequence|Mapping pattern:
    Tree of lists and dicts. Leaves are the names of variables.
    If a leaf is the empty string ``""``, it is ignored.
  :param function func:
    Takes a ``namedtuple`` of variables taken from the leaves of ``pattern``, and returns a query.
  """
  arg_names = sorted(_pattern_args(pattern))
  PatternArgs = namedtuple("PatternArgs", arg_names)
  args = PatternArgs(*[var(name) for name in arg_names])
  return lambda_expr(pattern, func(args))


def _pattern_args(pattern):
  """Collects all args from the leaves of a pattern."""
  args = []
  if isinstance(pattern, str):
    if pattern != "":
      args.append(pattern)
  elif isinstance(pattern, Sequence):
    for entry in pattern:
      args.extend(_pattern_args(entry))
  elif isinstance(pattern, Mapping):
    for entry in pattern.values():
      args.extend(_pattern_args(entry))
  else:
    raise InvalidQuery, "Pattern must be a str, Sequence, or Mapping; got %s" % repr(pattern)
  return args


def lambda_expr(var_name, expr):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return {"lambda": var_name, "expr": expr}

#endregion

#region Collection functions

def map_expr(lambda_expr, coll):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  # pylint: disable=redefined-outer-name
  return {"map": _to_lambda(lambda_expr), "collection": coll}


def foreach(lambda_expr, coll):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  # pylint: disable=redefined-outer-name
  return {"foreach": _to_lambda(lambda_expr), "collection": coll}


def filter_expr(lambda_expr, coll):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  # pylint: disable=redefined-outer-name
  return {"filter": _to_lambda(lambda_expr), "collection": coll}


def take(num, coll):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  return {"take": num, "collection": coll}


def drop(num, coll):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  return {"drop": num, "collection": coll}


def prepend(elems, collection):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  return {"prepend": elems, "collection": collection}


def append(elems, collection):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  return {"append": elems, "collection": collection}

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
  return {"create": class_ref, "params": params}


def update(ref, params):
  """See the `docs <https://faunadb.com/documentation/queries#write_functions>`__."""
  return {"update": ref, "params": params}


def replace(ref, params):
  """See the `docs <https://faunadb.com/documentation/queries#write_functions>`__."""
  return {"replace": ref, "params": params}


def delete(ref):
  """See the `docs <https://faunadb.com/documentation/queries#write_functions>`__."""
  return {"delete": ref}

#endregion

#region Sets

def match(matched, index):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return {"match": matched, "index": index}


def union(*sets):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return {"union": _varargs(sets)}


def intersection(*sets):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return {"intersection": _varargs(sets)}


def difference(*sets):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return {"difference": _varargs(sets)}


def join(source, target):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return {"join": source, "with": _to_lambda(target)}

#endregion

#region Miscellaneous Functions

def equals(*values):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"equals": _varargs(values)}


def concat(*strings):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"concat": _varargs(strings)}


def concat_with_separator(separator, *strings):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"concat": _varargs(strings), "separator": separator}


def contains(path, value):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"contains": path, "in": value}


def select(path, data):
  """
  See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__.
  See also :py:func:`select_with_default`."""
  return {"select": path, "from": data}


def select_with_default(path, data, default):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"select": path, "from": data, "default": default}


def add(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"add": _varargs(numbers)}


def multiply(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"multiply": _varargs(numbers)}


def subtract(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"subtract": _varargs(numbers)}


def divide(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"divide": _varargs(numbers)}


def modulo(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"modulo": _varargs(numbers)}


def and_expr(*booleans):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"and": _varargs(booleans)}


def or_expr(*booleans):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"or": _varargs(booleans)}


def not_expr(boolean):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return {"not": boolean}

#endregion

def _params(main_params, optional_params):
  """Hash of query arguments with None values removed."""
  for key, val in optional_params.iteritems():
    if val is not None:
      main_params[key] = val
  return main_params


def _varargs(values):
  """
  Called on ``*args`` arguments.
  This ensures that a single value passed is not put in an array, so
  ``query.add([1, 2])`` will work as well as ``query.add(1, 2)``.
  """
  return values[0] if len(values) == 1 else values
