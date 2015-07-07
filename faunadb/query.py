'''
Constructors for creating queries to be passed into Client.query.
See also use the constructors in faunadb.objects.
For query documentation see <https://faunadb.com/documentation#guide-queries>.
'''

# pylint: disable=invalid-name, missing-docstring, redefined-builtin

def let(vars, in_expr):
  return {"let": vars, "in": in_expr}

def var(var_name):
  return {"var": var_name}

def q_if(condition, true_expr, false_expr):
  return {"if": condition, "then": true_expr, "else": false_expr}

def do(expressions):
  return {"do": expressions}

def quote(expr):
  return {"quote": expr}

def q_lambda(var_name, expr):
  return {"lambda": var_name, "expr": expr}


# Collections

def map(lambda_expr, coll):
  return {"map": lambda_expr, "collection": coll}

def foreach(lambda_expr, coll):
  return {"foreach": lambda_expr, "collection": coll}


# Read functions

def get(ref, params=None):
  return _append_params({"get": ref}, params, ["ts"])

def paginate(set, params=None):
  return _append_params(
    {"paginate": set},
    params,
    ["ts", "after", "before", "size", "events", "sources"])

def exists(ref, params=None):
  return _append_params({"exists": ref}, params, ["ts"])

def count(set, params=None):
  _append_params({"count": set}, params, ["events"])


# Write functions

def create(class_ref, params):
  return {"create": class_ref, "params": params}

def update(ref, params):
  return {"update": ref, "params": params}

def replace(ref, params):
  return {"replace": ref, "params": params}

def delete(ref):
  return {"delete": ref}


# Sets

def union(sets):
  return {"union": sets}

def intersection(sets):
  return {"intersection": sets}

def difference(source, sets):
  return {"difference": [source] + sets}

def join(source, target):
  return {"join": source, "with": target}


# Miscellaneous Functions

def equals(values):
  return {"equals": values}

def concat(strings):
  return {"concat": strings}

def contains(path, value):
  return {"contains": path, "in": value}

def select(path, data, params=None):
  return _append_params(
    {"select": path, "from": data},
    params,
    ["ts", "after", "before", "size", "events", "sources"])

def add(numbers):
  return {"add": numbers}

def multiply(numbers):
  return {"multiply": numbers}

def subtract(numbers):
  return {"subtract": numbers}

def divide(numbers):
  return {"divide": numbers}


def _append_params(source, params, allowed_params):
  if params is not None:
    source.update(params)
  return source
