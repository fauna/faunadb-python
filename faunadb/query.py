"""
Constructors for creating queries to be passed into Client.query.
See also use the constructors in faunadb.objects.
For query documentation see <https://faunadb.com/documentation#guide-queries>.

When constructing queries, you must use these functions or constructors from objects.py.
For passing raw data to a query, use query.object or query.quote.
"""

from .errors import InvalidQuery

# pylint: disable=invalid-name, redefined-builtin

#region Basic forms

def let(vars, in_expr):
  "See https://faunadb.com/documentation#queries-basic_forms."
  return {"let": vars, "in": in_expr}

def var(var_name):
  "See https://faunadb.com/documentation#queries-basic_forms."
  return {"var": var_name}

def if_expr(condition, true_expr, false_expr):
  "See https://faunadb.com/documentation#queries-basic_forms."
  return {"if": condition, "then": true_expr, "else": false_expr}

def do(expressions):
  "See https://faunadb.com/documentation#queries-basic_forms."
  return {"do": expressions}

def object(**keys_vals):
  "See https://faunadb.com/documentation#queries-basic_forms."
  return {"object": keys_vals}

def quote(expr):
  "See https://faunadb.com/documentation#queries-basic_forms."
  return {"quote": expr}

def lambda_expr(var_name, expr):
  "See https://faunadb.com/documentation#queries-basic_forms."
  return {"lambda": var_name, "expr": expr}

#endregion

#region Collection functions

def map(lambda_expr, coll):
  "See https://faunadb.com/documentation#queries-collection_functions."
  # pylint: disable=redefined-outer-name
  return {"map": lambda_expr, "collection": coll}

def foreach(lambda_expr, coll):
  "See https://faunadb.com/documentation#queries-collection_functions."
  # pylint: disable=redefined-outer-name
  return {"foreach": lambda_expr, "collection": coll}

#endregion

#region Read functions

def get(ref, params=None):
  "See https://faunadb.com/documentation#queries-read_functions."
  return _append_params({"get": ref}, params, ["ts"])

def paginate(set, params=None):
  "See https://faunadb.com/documentation#queries-read_functions."
  return _append_params(
    {"paginate": set},
    params,
    ["ts", "after", "before", "size", "events", "sources"])

def exists(ref, params=None):
  "See https://faunadb.com/documentation#queries-read_functions."
  return _append_params({"exists": ref}, params, ["ts"])

def count(set, params=None):
  "See https://faunadb.com/documentation#queries-read_functions."
  _append_params({"count": set}, params, ["events"])

#endregion

#region Write functions

def create(class_ref, params=None):
  """
  See https://faunadb.com/documentation#queries-write_functions.
  See also Model.create.
  """
  return {"create": class_ref, "params": params or {}}

def update(ref, params=None):
  """
  See https://faunadb.com/documentation#queries-write_functions.
  See also Model.patch.
  """
  return {"update": ref, "params": params or {}}

def replace(ref, params=None):
  """
  See https://faunadb.com/documentation#queries-write_functions.
  See also Model.put.
  """
  return {"replace": ref, "params": params or {}}

def delete(ref):
  """
  See https://faunadb.com/documentation#queries-write_functions.
  See also Model.delete.
  """
  return {"delete": ref}

#endregion

#region Set functions

def union(sets):
  "See https://faunadb.com/documentation#queries-sets."
  return {"union": sets}

def intersection(sets):
  "See https://faunadb.com/documentation#queries-sets."
  return {"intersection": sets}

def difference(source, sets):
  "See https://faunadb.com/documentation#queries-sets."
  return {"difference": [source] + sets}

def join(source, target):
  "See https://faunadb.com/documentation#queries-sets."
  return {"join": source, "with": target}

#endregion

#region Miscellaneous Functions

def equals(values):
  "See https://faunadb.com/documentation#queries-misc_functions."
  return {"equals": values}

def concat(strings):
  "See https://faunadb.com/documentation#queries-misc_functions."
  return {"concat": strings}

def contains(path, value):
  "See https://faunadb.com/documentation#queries-misc_functions."
  return {"contains": path, "in": value}

def select(path, data, params=None):
  "See https://faunadb.com/documentation#queries-misc_functions."
  return _append_params(
    {"select": path, "from": data},
    params,
    ["ts", "after", "before", "size", "events", "sources"])

def add(numbers):
  "See https://faunadb.com/documentation#queries-misc_functions."
  return {"add": numbers}

def multiply(numbers):
  "See https://faunadb.com/documentation#queries-misc_functions."
  return {"multiply": numbers}

def subtract(numbers):
  "See https://faunadb.com/documentation#queries-misc_functions."
  return {"subtract": numbers}

def divide(numbers):
  "See https://faunadb.com/documentation#queries-misc_functions."
  return {"divide": numbers}

#endregion

def _append_params(source, params, allowed_params):
  "Puts parameters into a query expression."
  if params is not None:
    for param in params:
      if param not in allowed_params:
        raise InvalidQuery("%s is not a valid parameter." % param)
    source.update(params)
  return source
