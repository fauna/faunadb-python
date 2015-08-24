"""
Constructors for creating queries to be passed into Client.query.
See also use the constructors in faunadb.objects.
For query documentation see <https://faunadb.com/documentation#queries>.

When constructing queries, you must use these functions or constructors from objects.py.
For passing raw data to a query, use query.object or query.quote.
"""

# pylint: disable=invalid-name, redefined-builtin

NoVal = object()

#region Basic forms

def let(vars, in_expr):
  """See https://faunadb.com/documentation#queries-basic_forms."""
  return {"let": vars, "in": in_expr}


def var(var_name):
  """See https://faunadb.com/documentation#queries-basic_forms."""
  return {"var": var_name}


def if_expr(condition, true_expr, false_expr):
  """See https://faunadb.com/documentation#queries-basic_forms."""
  return {"if": condition, "then": true_expr, "else": false_expr}


def do(expressions):
  """See https://faunadb.com/documentation#queries-basic_forms."""
  return {"do": expressions}


def object(**keys_vals):
  """See https://faunadb.com/documentation#queries-basic_forms."""
  return {"object": keys_vals}


def quote(expr):
  """See https://faunadb.com/documentation#queries-basic_forms."""
  return {"quote": expr}


def lambda_expr(var_name, expr):
  """See https://faunadb.com/documentation#queries-basic_forms."""
  return {"lambda": var_name, "expr": expr}

#endregion

#region Collection functions

def map(lambda_expr, coll):
  """See https://faunadb.com/documentation#queries-collection_functions."""
  # pylint: disable=redefined-outer-name
  return {"map": lambda_expr, "collection": coll}


def foreach(lambda_expr, coll):
  """See https://faunadb.com/documentation#queries-collection_functions."""
  # pylint: disable=redefined-outer-name
  return {"foreach": lambda_expr, "collection": coll}

#endregion

#region Read functions

def get(ref, ts=NoVal):
  """See https://faunadb.com/documentation#queries-read_functions."""
  return _params(get=ref, ts=ts)

def paginate(
    set, size=NoVal, ts=NoVal, after=NoVal, before=NoVal, events=NoVal, sources=NoVal):
  """See https://faunadb.com/documentation#queries-read_functions."""
  # pylint: disable=too-many-arguments
  return _params(
    paginate=set, size=size, ts=ts, after=after, before=before, events=events, sources=sources)


def exists(ref, ts=NoVal):
  """See https://faunadb.com/documentation#queries-read_functions."""
  return _params(exists=ref, ts=ts)


def count(set, events=NoVal):
  """See https://faunadb.com/documentation#queries-read_functions."""
  return _params(count=set, events=events)

#endregion

#region Write functions

def create(class_ref, params=NoVal):
  """
  See https://faunadb.com/documentation#queries-write_functions.
  See also Model.create.
  """
  return {"create": class_ref, "params": params or {}}


def update(ref, params=NoVal):
  """See https://faunadb.com/documentation#queries-write_functions."""
  return {"update": ref, "params": params or {}}


def replace(ref, params=NoVal):
  """See https://faunadb.com/documentation#queries-write_functions."""
  return {"replace": ref, "params": params or {}}


def delete(ref):
  """See https://faunadb.com/documentation#queries-write_functions."""
  return {"delete": ref}

#endregion

#region Miscellaneous Functions

def equals(values):
  """See https://faunadb.com/documentation#queries-misc_functions."""
  return {"equals": values}


def concat(strings):
  """See https://faunadb.com/documentation#queries-misc_functions."""
  return {"concat": strings}


def contains(path, value):
  """See https://faunadb.com/documentation#queries-misc_functions."""
  return {"contains": path, "in": value}


def select(path, data, default=NoVal):
  """See https://faunadb.com/documentation#queries-misc_functions."""
  return _params(**{"select": path, "from": data, "default": default})


def add(numbers):
  """See https://faunadb.com/documentation#queries-misc_functions."""
  return {"add": numbers}


def multiply(numbers):
  """See https://faunadb.com/documentation#queries-misc_functions."""
  return {"multiply": numbers}


def subtract(numbers):
  """See https://faunadb.com/documentation#queries-misc_functions."""
  return {"subtract": numbers}


def divide(numbers):
  """See https://faunadb.com/documentation#queries-misc_functions."""
  return {"divide": numbers}

#endregion

def _params(**kwargs):
  """Hash of query arguments with NoVal values removed."""
  return {k: v for k, v in kwargs.iteritems() if v is not NoVal}
