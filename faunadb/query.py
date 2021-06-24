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
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/abort>`__."""
  return _fn({"abort": msg})

def ref(collection_ref, id=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/ref>`__."""
  if id is None:
    return _fn({"@ref": collection_ref})
  return _fn({"ref": collection_ref, "id": id})


@deprecated("use collections instead")
def classes(scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/classes>`__."""
  return _fn({"classes": scope})

def collections(scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/collections>`__."""
  return _fn({"collections": scope})


def documents(collections):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/documents>`__."""
  return _fn({"documents": collections})


def databases(scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/databases>`__."""
  return _fn({"databases": scope})

def indexes(scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/indexes>`__."""
  return _fn({"indexes": scope})

def functions(scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/functions>`__."""
  return _fn({"functions": scope})

def roles(scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/roles>`__."""
  return _fn({"roles": scope})

def access_providers(scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/access_providers>`__."""
  return _fn({"access_providers": scope})

def keys(scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/keys>`__."""
  return _fn({"keys": scope})

def tokens(scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/tokens>`__."""
  return _fn({"tokens": scope})

def credentials(scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/credentials>`__."""
  return _fn({"credentials": scope})

def at(timestamp, expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/at>`__."""
  return _fn({"at": timestamp, "expr": expr})

class LetBindings:
  def __init__(self, bindings):
    self._bindings = bindings
  def in_(self, in_expr):
    return _fn({"let": self._bindings, "in": in_expr})


def let(*args, **kwargs):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/let>`__."""
  if kwargs:
    return LetBindings([_fn({k: v}) for k, v in kwargs.items()])
  else:
    bindings = [_fn({k: v}) for k, v in args[0].items()]
    in_expr = args[1]
    return _fn({"let": bindings, "in": in_expr})


def var(var_name):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/var>`__."""
  return _fn({"var": var_name})


@deprecated("use if_ instead")
def if_expr(condition, then, else_):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/if>`__."""
  return if_(condition, then, else_)


def if_(condition, then, else_):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/if>`__."""
  return _fn({"if": condition, "then": then, "else": else_})


def do(*expressions):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/do>`__."""
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
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/lambda>`__."""
  return lambda_(var_name_or_pattern, expr)


def lambda_(var_name_or_pattern, expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/lambda>`__."""
  return _fn({"lambda": var_name_or_pattern, "expr": expr})


def call(ref_, *arguments):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/call>`__."""
  return _fn({"call": ref_, "arguments": _varargs(arguments)})


def query(_lambda):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/query>`__."""
  if isinstance(_lambda, FunctionType):
    _lambda = lambda_query(_lambda)
  return _fn({"query": _lambda})

#endregion

#region Collection functions

@deprecated("use map_ instead")
def map_expr(expr, collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/map>`__."""
  return map_(expr, collection)


def map_(expr, collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/map>`__."""
  return _fn({"map": expr, "collection": collection})


def foreach(expr, collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/foreach>`__."""
  return _fn({"foreach": expr, "collection": collection})


@deprecated("use filter_ instead")
def filter_expr(expr, collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/filter>`__."""
  return filter_(expr, collection)


def filter_(expr, collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/filter>`__."""
  return _fn({"filter": expr, "collection": collection})


def take(number, collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/take>`__."""
  return _fn({"take": number, "collection": collection})


def drop(number, collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/drop>`__."""
  return _fn({"drop": number, "collection": collection})


def prepend(elements, collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/prepend>`__."""
  return _fn({"prepend": elements, "collection": collection})


def append(elements, collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/append>`__."""
  return _fn({"append": elements, "collection": collection})

def is_empty(collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isempty>`__."""
  return _fn({"is_empty": collection})

def is_nonempty(collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isnonempty>`__."""
  return _fn({"is_nonempty": collection})

#endregion

#region Type functions

def is_number(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isnumber>`__."""
  return _fn({"is_number": expr})

def is_double(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isdouble>`__."""
  return _fn({"is_double": expr})

def is_integer(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isinteger>`__."""
  return _fn({"is_integer": expr})

def is_boolean(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isboolean>`__."""
  return _fn({"is_boolean": expr})

def is_null(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isnull>`__."""
  return _fn({"is_null": expr})

def is_bytes(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isbytes>`__."""
  return _fn({"is_bytes": expr})

def is_timestamp(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/istimestamp>`__."""
  return _fn({"is_timestamp": expr})

def is_date(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isdate>`__."""
  return _fn({"is_date": expr})

def is_string(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isstring>`__."""
  return _fn({"is_string": expr})

def is_array(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isarray>`__."""
  return _fn({"is_array": expr})

def is_object(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isobject>`__."""
  return _fn({"is_object": expr})

def is_ref(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isref>`__."""
  return _fn({"is_ref": expr})

def is_set(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isset>`__."""
  return _fn({"is_set": expr})

def is_doc(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isdoc>`__."""
  return _fn({"is_doc": expr})

def is_lambda(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/islambda>`__."""
  return _fn({"is_lambda": expr})

def is_collection(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/iscollection>`__."""
  return _fn({"is_collection": expr})

def is_database(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isdatabase>`__."""
  return _fn({"is_database": expr})

def is_index(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isindex>`__."""
  return _fn({"is_index": expr})

def is_function(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isfunction>`__."""
  return _fn({"is_function": expr})

def is_key(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/iskey>`__."""
  return _fn({"is_key": expr})

def is_token(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/istoken>`__."""
  return _fn({"is_token": expr})

def is_credentials(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/iscredentials>`__."""
  return _fn({"is_credentials": expr})

def is_role(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/isrole>`__."""
  return _fn({"is_role": expr})

#endregion

#region Read functions

def get(ref_, ts=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/get>`__."""
  return _params({"get": ref_}, {"ts": ts})


def key_from_secret(secret):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/keyfromsecret>`__."""
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
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/exists>`__."""
  return _params({"exists": ref_}, {"ts": ts})

#endregion

#region Write functions

def create(collection_ref, params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/create>`__."""
  return _fn({"create": collection_ref, "params": params})


def update(ref_, params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/update>`__."""
  return _fn({"update": ref_, "params": params})


def replace(ref_, params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/replace>`__."""
  return _fn({"replace": ref_, "params": params})


def delete(ref_):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/delete>`__."""
  return _fn({"delete": ref_})


def insert(ref_, ts, action, params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/insert>`__."""
  return _fn({"insert": ref_, "ts": ts, "action": action, "params": params})


def remove(ref_, ts, action):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/remove>`__."""
  return _fn({"remove": ref_, "ts": ts, "action": action})

@deprecated("use create_collection instead")
def create_class(class_params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/create_class>`__."""
  return _fn({"create_class": class_params})

def create_collection(collection_params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/createcollection>`__."""
  return _fn({"create_collection": collection_params})

def create_database(db_params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/createdatabase>`__."""
  return _fn({"create_database": db_params})


def create_index(index_params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/createindex>`__."""
  return _fn({"create_index": index_params})


def create_function(func_params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/createfunction>`__."""
  return _fn({"create_function": func_params})


def create_role(func_params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/createrole>`__."""
  return _fn({"create_role": func_params})

def create_access_provider(provider_params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/createaccessprovider>`__."""
  return _fn({"create_access_provider": provider_params})

def move_database(from_, to):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/movedatabase>`__."""
  return _fn({"move_database": from_, "to": to})


def create_key(key_params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/createkey>`__."""
  return _fn({"create_key": key_params})

#endregion

#region Sets

def singleton(ref_):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/singleton>`__."""
  return _fn({"singleton": ref_})


def events(ref_set):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/events>`__."""
  return _fn({"events": ref_set})


def match(index, *terms):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/match>`__."""
  # pylint: disable=redefined-outer-name
  m = {"match": index}

  if len(terms) >= 1:
    m["terms"] = _varargs(terms)

  return _fn(m)


def reverse(set_array_or_page):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/reverse>`__."""
  return _fn({"reverse": set_array_or_page})

def merge(merge, with_, lambda_=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/merge>`__."""
  return _params({"merge": merge, "with": with_}, {"lambda": lambda_})

def union(*sets):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/union>`__."""
  return _fn({"union": _varargs(sets)})

def reduce(lambda_, initial, collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/reduce>`__."""
  return _fn({"reduce": lambda_, "initial": initial, "collection": collection})


def intersection(*sets):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/intersection>`__."""
  return _fn({"intersection": _varargs(sets)})


def difference(*sets):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/difference>`__."""
  return _fn({"difference": _varargs(sets)})


def distinct(set):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/distinct>`__."""
  return _fn({"distinct": set})


def join(source, target):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/join>`__."""
  return _fn({"join": source, "with": target})

def range(set, from_, to):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/range>`__."""
  return _fn({"range": set, "from": from_, "to": to})


#endregion

#region Authentication

def login(ref_, params):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/login>`__."""
  return _fn({"login": ref_, "params": params})


def logout(delete_tokens):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/logout>`__."""
  return _fn({"logout": delete_tokens})


def identify(ref_, password):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/identify>`__."""
  return _fn({"identify": ref_, "password": password})

@deprecated("Use `current_identity` instead")
def identity():
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/identity>`__."""
  return _fn({"identity": None})


def current_identity():
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/current_identity>`__."""
  return _fn({"current_identity": None})


def has_current_identity():
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/has_current_identity>`__."""
  return _fn({"has_current_identity": None})


def current_token():
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/current_token>`__."""
  return _fn({"current_token": None})


def has_current_token():
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/has_current_token>`__."""
  return _fn({"has_current_token": None})


def has_identity():
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/hasidentity>`__."""
  return _fn({"has_identity": None})

#endregion

#region String functions

def format(string, *values):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/format>`__."""
  return _fn({"format": string, "values": _varargs(values)})


def concat(strings, separator=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/concat>`__."""
  return _params({"concat": strings}, {"separator": separator})


def casefold(string, normalizer=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/casefold>`__."""
  return _params({"casefold": string}, {"normalizer": normalizer})


def starts_with(value, search):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/startswith>`__."""
  return _fn({"startswith": value, "search": search})


def ends_with(value, search):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/endswith>`__."""
  return _fn({"endswith": value, "search": search})


def contains_str(value, search):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/containsstr>`__."""
  return _fn({"containsstr": value, "search": search})


def contains_str_regex(value, pattern):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/containsstrregex>`__."""
  return _fn({"containsstrregex": value, "pattern": pattern})


def regex_escape(value):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/regexescape>`__."""
  return _fn({"regexescape": value})


def ngram(terms, min=None, max=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/ngram>`__."""
  return _params({"ngram": terms}, {"min": min, "max": max})


def find_str(value, find, start=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/findstr>`__."""
  return _params({"findstr": value, "find": find}, {"start": start})


def find_str_regex(value, pattern, start=None, numResults=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/findstrregex>`__."""
  return _params({"findstrregex": value, "pattern": pattern}, {"start": start, "num_results": numResults})


def replace_str(value, find, replace):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/replacestr>`__."""
  return _fn({"replacestr": value, "find": find, "replace": replace})


def replace_str_regex(value, pattern, replace, first=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/replacestrregex>`__."""
  return _params({"replacestrregex": value, "pattern": pattern, "replace": replace}, {"first": first})


def length(value):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/length>`__."""
  return _fn({"length": value})


def lowercase(value):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/lowercase>`__."""
  return _fn({"lowercase": value})


def uppercase(value):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/uppercase>`__."""
  return _fn({"uppercase": value})


def titlecase(value):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/titlecase>`__."""
  return _fn({"titlecase": value})


def trim(value):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/trim>`__."""
  return _fn({"trim": value})


def ltrim(value):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/ltrim>`__."""
  return _fn({"ltrim": value})


def rtrim(value):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/rtrim>`__."""
  return _fn({"rtrim": value})


def space(count):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/space>`__."""
  return _fn({"space": count})


def substring(value, start, length=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/substring>`__."""
  return _params({"substring": value, "start": start}, {"length": length})


def repeat(value, number=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/repeat>`__."""
  return _params({"repeat": value}, {"number": number})

#endregion

#region Time and date functions

def time(string):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/time>`__."""
  return _fn({"time": string})


def epoch(number, unit):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/epoch>`__."""
  return _fn({"epoch": number, "unit": unit})


def now():
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/date>`__."""
  return _fn({"now": None})

def date(string):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/date>`__."""
  return _fn({"date": string})


def time_add(base, offset, unit):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/timeadd>`__."""
  return _fn({
		"time_add": base,
		"offset": offset,
		"unit": unit
  })


def time_subtract(base, offset, unit):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/timesubtract>`__."""
  return _fn({
    "time_subtract": base,
    "offset": offset,
    "unit": unit,
  })


def time_diff(start, finish, unit):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/timediff>`__."""
  return _fn({
		"time_diff": start,
		"other": finish,
		"unit": unit,
  })

#endregion

#region Miscellaneous functions

@deprecated("use new_id instead")
def next_id():
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/nextid>`__."""
  return _fn({"next_id": None})


def new_id():
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/newid>`__."""
  return _fn({"new_id": None})


def database(db_name, scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/database>`__."""
  return _params({"database": db_name}, {"scope": scope})


def index(index_name, scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/index>`__."""
  return _params({"index": index_name}, {"scope": scope})


@deprecated("use collection instead")
def class_expr(class_name, scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/class>`__."""
  return class_(class_name, scope)

@deprecated("use collection instead")
def class_(class_name, scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/class>`__."""
  return _params({"class": class_name}, {"scope": scope})

def collection(collection_name, scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/collection>`__."""
  return _params({"collection": collection_name}, {"scope": scope})

def function(fn_name, scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/function>`__."""
  return _params({"function": fn_name}, {"scope": scope})


def role(role_name, scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/role>`__."""
  return _params({"role": role_name}, {"scope": scope})


def access_provider(access_provider_name, scope=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/access_provider>`__."""
  return _params({"access_provider": access_provider_name}, {"scope": scope})


def equals(*values):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/equals>`__."""
  return _fn({"equals": _varargs(values)})

@deprecated("use `contains_path` instead.")
def contains(path, in_):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/contains>`__."""
  return _fn({"contains": path, "in": in_})


def contains_path(path, in_):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/containspath>`__."""
  return _fn({"contains_path": path, "in": in_})

def contains_field(field, in_):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/containsfield>`__."""
  return _fn({"contains_field": field, "in": in_})

def contains_value(value, in_):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/containsvalue>`__."""
  return _fn({"contains_value": value, "in": in_})

_NO_DEFAULT = object()

def select(path, from_, default=_NO_DEFAULT):
  """
  See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/select>`__.
  See also :py:func:`select_with_default`."""
  _dict = {"select": path, "from": from_}
  if default is not _NO_DEFAULT:
    _dict["default"] = default
  return _fn(_dict)


@deprecated("Use `select` instead")
def select_with_default(path, from_, default):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/select>`__."""
  return _fn({"select": path, "from": from_, "default": default})


def select_all(path, from_):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/selectall>`__."""
  return _fn({"select_all": path, "from": from_})


def add(*numbers):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/add>`__."""
  return _fn({"add": _varargs(numbers)})


def multiply(*numbers):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/multiply>`__."""
  return _fn({"multiply": _varargs(numbers)})


def subtract(*numbers):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/subtract>`__."""
  return _fn({"subtract": _varargs(numbers)})


def divide(*numbers):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/divide>`__."""
  return _fn({"divide": _varargs(numbers)})


def pow(base, exp):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/pow>` __."""
  return _fn({"pow": base, "exp": exp})


def max(*numbers):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/max>` __."""
  return _fn({"max": _varargs(numbers)})


def min(*numbers):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/min>` __."""
  return _fn({"min": _varargs(numbers)})

def abs(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/abs>` __."""
  return _fn({"abs": num})


def trunc(num, precision=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/trunc>` __."""
  return _params({"trunc": num}, {"precision": precision})


def bitor(*numbers):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/bitor>` __."""
  return _fn({"bitor": _varargs(numbers)})


def cosh(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/cosh>` __."""
  return _fn({"cosh": num})


def hypot(num, b):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/hypot>` __."""
  return _fn({"hypot": num, "b": b})


def atan(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/atan>` __."""
  return _fn({"atan": num})


def log(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/log>` __."""
  return _fn({"log": num})


def bitnot(*num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/bitnot>` __."""
  return _fn({"bitnot": _varargs(num)})


def bitxor(*num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/bitxor>` __."""
  return _fn({"bitxor": _varargs(num)})


def bitand(*num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/bitand>` __."""
  return _fn({"bitand": _varargs(num)})


def ceil(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/ceil>` __."""
  return _fn({"ceil": num})


def degrees(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/degrees>` __."""
  return _fn({"degrees": num})


def cos(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/cos>` __."""
  return _fn({"cos": num})


def acos(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/acos>` __."""
  return _fn({"acos": num})


def sqrt(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/sqrt>` __."""
  return _fn({"sqrt": num})


def tan(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/tan>` __."""
  return _fn({"tan": num})


def tanh(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/tanh>` __."""
  return _fn({"tanh": num})


def sin(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/sin>` __."""
  return _fn({"sin": num})


def asin(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/asin>` __."""
  return _fn({"asin": num})


def round(num, precision=None):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/round>` __."""
  return _params({"round": num}, {"precision": precision})


def radians(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/radians>` __."""
  return _fn({"radians": num})

def floor(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/floor>` __."""
  return _fn({"floor": num})


def sign(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/sign>` __."""
  return _fn({"sign": num})


def exp(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/exp>` __."""
  return _fn({"exp": num})


def ln(num):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/ln>` __."""
  return _fn({"ln": num})


def any(collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/any>`__."""
  return _fn({"any": collection})


def all(collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/all>`__."""
  return _fn({"all": collection})


def modulo(*numbers):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/modulo>`__."""
  return _fn({"modulo": _varargs(numbers)})


def count(collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/count>`__."""
  return _fn({"count": collection})

def sum(collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/sum>`__."""
  return _fn({"sum": collection})

def mean(collection):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/mean>`__."""
  return _fn({"mean": collection})


def lt(*values):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/lt>`__."""
  return _fn({"lt": _varargs(values)})


def lte(*values):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/lte>`__."""
  return _fn({"lte": _varargs(values)})


def gt(*values):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/gt>`__."""
  return _fn({"gt": _varargs(values)})


def gte(*values):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/gte>`__."""
  return _fn({"gte": _varargs(values)})


@deprecated("use and_ instead")
def and_expr(*booleans):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/and>`__."""
  return and_(*booleans)


def and_(*booleans):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/and>`__."""
  return _fn({"and": _varargs(booleans)})


@deprecated("use or_ instead")
def or_expr(*booleans):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/or>`__."""
  return or_(*booleans)


def or_(*booleans):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/or>`__."""
  return _fn({"or": _varargs(booleans)})


@deprecated("use not_ instead")
def not_expr(boolean):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/not>`__."""
  return not_(boolean)


def not_(boolean):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/not>`__."""
  return _fn({"not": boolean})

def to_string(expr):
  return _fn({"to_string": expr})

def to_array(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/toarray>`__."""
  return _fn({"to_array": expr})

def to_object(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/toobject>`__."""
  return _fn({"to_object": expr})

def to_double(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/todouble>`__."""
  return _fn({"to_double": expr})

def to_integer(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/tointeger>`__."""
  return _fn({"to_integer": expr})

def to_number(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/tonumber>`__."""
  return _fn({"to_number": expr})

def to_time(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/totime>`__."""
  return _fn({"to_time": expr})

def to_seconds(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/toseconds>`__."""
  return _fn({"to_seconds": expr})

def to_millis(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/tomillis>`__."""
  return _fn({"to_millis": expr})

def to_micros(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/tomicros>`__."""
  return _fn({"to_micros": expr})

def day_of_month(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/dayofmonth>`__."""
  return _fn({"day_of_month": expr})

def day_of_week(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/dayofweek>`__."""
  return _fn({"day_of_week": expr})

def day_of_year(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/dayofyear>`__."""
  return _fn({"day_of_year": expr})

def year(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/year>`__."""
  return _fn({"year": expr})

def month(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/month>`__."""
  return _fn({"month": expr})

def hour(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/hour>`__."""
  return _fn({"hour": expr})

def minute(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/minute>`__."""
  return _fn({"minute": expr})

def second(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/second>`__."""
  return _fn({"second": expr})

def to_date(expr):
  """See the `docs <https://docs.fauna.com/fauna/current/api/fql/functions/todate>`__."""
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
