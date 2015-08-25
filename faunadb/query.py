"""
Constructors for creating queries to be passed into Client.query.
See also use the constructors in faunadb.objects.
For query documentation see the `docs <https://faunadb.com/documentation#queries>`_.

When constructing queries, you must use these functions or constructors from :doc:`objects`.
To pass raw data to a query, use :any:`object` or :any:`quote`.
"""

# pylint: disable=invalid-name, redefined-builtin

# Give NoVal a __repr__ method so that it shows up as "NoVal" in documentation.
class _NoValClass(object):
  # pylint: disable=no-init
  def __repr__(self):
    return "NoVal"
NoVal = _NoValClass()


#region Basic forms

def let(vars, in_expr):
  """See the `docs <https://faunadb.com/documentation#queries-basic_forms>`__."""
  return {"let": vars, "in": in_expr}


def var(var_name):
  """See the `docs <https://faunadb.com/documentation#queries-basic_forms>`__."""
  return {"var": var_name}


def if_expr(condition, true_expr, false_expr):
  """See the `docs <https://faunadb.com/documentation#queries-basic_forms>`__."""
  return {"if": condition, "then": true_expr, "else": false_expr}


def do(expressions):
  """See the `docs <https://faunadb.com/documentation#queries-basic_forms>`__."""
  return {"do": expressions}


def object(**keys_vals):
  """See the `docs <https://faunadb.com/documentation#queries-basic_forms>`__."""
  return {"object": keys_vals}


def quote(expr):
  """See the `docs <https://faunadb.com/documentation#queries-basic_forms>`__."""
  return {"quote": expr}


def lambda_expr(var_name, expr):
  """See the `docs <https://faunadb.com/documentation#queries-basic_forms>`__."""
  return {"lambda": var_name, "expr": expr}

#endregion

#region Collection functions

def map(lambda_expr, coll):
  """See the `docs <https://faunadb.com/documentation#queries-collection_functions>`__."""
  # pylint: disable=redefined-outer-name
  return {"map": lambda_expr, "collection": coll}


def foreach(lambda_expr, coll):
  """See the `docs <https://faunadb.com/documentation#queries-collection_functions>`__."""
  # pylint: disable=redefined-outer-name
  return {"foreach": lambda_expr, "collection": coll}

#endregion

#region Read functions

def get(ref, ts=NoVal):
  """See the `docs <https://faunadb.com/documentation#queries-read_functions>`__."""
  return _params(get=ref, ts=ts)

def paginate(
    set, size=NoVal, ts=NoVal, after=NoVal, before=NoVal, events=NoVal, sources=NoVal):
  """
  See the `docs <https://faunadb.com/documentation#queries-read_functions>`__.
  You may want to convert the result of this to a :any:`Page`.
  """
  # pylint: disable=too-many-arguments
  return _params(
    paginate=set, size=size, ts=ts, after=after, before=before, events=events, sources=sources)


def exists(ref, ts=NoVal):
  """See the `docs <https://faunadb.com/documentation#queries-read_functions>`__."""
  return _params(exists=ref, ts=ts)


def count(set, events=NoVal):
  """See the `docs <https://faunadb.com/documentation#queries-read_functions>`__."""
  return _params(count=set, events=events)

#endregion

#region Write functions

def create(class_ref, params=NoVal):
  """See the `docs <https://faunadb.com/documentation#queries-write_functions>`__."""
  return {"create": class_ref, "params": params or {}}


def update(ref, params=NoVal):
  """See the `docs <https://faunadb.com/documentation#queries-write_functions>`__."""
  return {"update": ref, "params": params or {}}


def replace(ref, params=NoVal):
  """See the `docs <https://faunadb.com/documentation#queries-write_functions>`__."""
  return {"replace": ref, "params": params or {}}


def delete(ref):
  """See the `docs <https://faunadb.com/documentation#queries-write_functions>`__."""
  return {"delete": ref}

#endregion

#region Miscellaneous Functions

def equals(values):
  """See the `docs <https://faunadb.com/documentation#queries-misc_functions>`__."""
  return {"equals": values}


def concat(strings):
  """See the `docs <https://faunadb.com/documentation#queries-misc_functions>`__."""
  return {"concat": strings}


def contains(path, value):
  """See the `docs <https://faunadb.com/documentation#queries-misc_functions>`__."""
  return {"contains": path, "in": value}


def select(path, data, default=NoVal):
  """See the `docs <https://faunadb.com/documentation#queries-misc_functions>`__."""
  return _params(**{"select": path, "from": data, "default": default})


def add(numbers):
  """See the `docs <https://faunadb.com/documentation#queries-misc_functions>`__."""
  return {"add": numbers}


def multiply(numbers):
  """See the `docs <https://faunadb.com/documentation#queries-misc_functions>`__."""
  return {"multiply": numbers}


def subtract(numbers):
  """See the `docs <https://faunadb.com/documentation#queries-misc_functions>`__."""
  return {"subtract": numbers}


def divide(numbers):
  """See the `docs <https://faunadb.com/documentation#queries-misc_functions>`__."""
  return {"divide": numbers}

#endregion

def _params(**kwargs):
  """Hash of query arguments with NoVal values removed."""
  return {k: v for k, v in kwargs.iteritems() if v is not NoVal}
