"""
Constructors for creating queries to be passed into Client.query.
For query documentation see the `docs <https://faunadb.com/documentation/queries>`_.

When constructing queries, you must use these functions or
the :any:`Ref`, :any:`Set`, and :any:`Event` constructors.
To pass raw data to a query, use :any:`object` or :any:`quote`.
"""

# pylint: disable=invalid-name, redefined-builtin

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
  return _varargs_query("do", expressions)


def object(**keys_vals):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return {"object": keys_vals}


def quote(expr):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return {"quote": expr}


def lambda_expr(var_name, expr):
  """See the `docs <https://faunadb.com/documentation/queries#basic_forms>`__."""
  return {"lambda": var_name, "expr": expr}

#endregion

#region Collection functions

def map(lambda_expr, coll):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  # pylint: disable=redefined-outer-name
  return {"map": lambda_expr, "collection": coll}


def foreach(lambda_expr, coll):
  """See the `docs <https://faunadb.com/documentation/queries#collection_functions>`__."""
  # pylint: disable=redefined-outer-name
  return {"foreach": lambda_expr, "collection": coll}

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
  return _varargs_query("union", sets)


def intersection(*sets):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return _varargs_query("intersection", sets)


def difference(*sets):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return _varargs_query("difference", sets)


def join(source, target):
  """See the `docs <https://faunadb.com/documentation/queries#sets>`__."""
  return {"join": source, "with": target}

#endregion

#region Miscellaneous Functions

def equals(*values):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _varargs_query("equals", values)


def concat(*strings):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _varargs_query("concat", strings)


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
  return _varargs_query("add", numbers)


def multiply(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _varargs_query("multiply", numbers)


def subtract(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _varargs_query("subtract", numbers)


def divide(*numbers):
  """See the `docs <https://faunadb.com/documentation/queries#misc_functions>`__."""
  return _varargs_query("divide", numbers)

#endregion

def _params(main_params, optional_params):
  """Hash of query arguments with None values removed."""
  for key in optional_params:
    val = optional_params[key]
    if val is not None:
      main_params[key] = val
  return main_params


def _varargs_query(name, values):
  """
  Call name with varargs.
  This ensures that a single value passed is not put in array, so
  :samp:`query.add(query.var(x))` will work where :samp:`x` is a list whose values are to be added.
  """
  return {name: values[0] if len(values) == 1 else values}
