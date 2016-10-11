from datetime import date, datetime
from json import dumps, loads, JSONEncoder
from iso8601 import parse_date

from faunadb.objects import Ref, SetRef
from faunadb.query import _Expr


def parse_json(json_string):
  """
  Parses a JSON string into python values.
  Also parses :any:`Ref`, :any:`SetRef`, :class:`datetime` and :class:`date`.
  """
  return loads(json_string, object_hook=_parse_json_hook)


def parse_json_or_none(json_string):
  try:
    return parse_json(json_string)
  except ValueError:
    return None


def _parse_json_hook(dct):
  """
  Looks for FaunaDB types in a JSON object and converts to them if possible.
  """
  if "@ref" in dct:
    return Ref(dct["@ref"])
  if "@obj" in dct:
    return dct["@obj"]
  if "@set" in dct:
    return SetRef(dct["@set"])
  if "@ts" in dct:
    return parse_date(dct["@ts"])
  if "@date" in dct:
    return parse_date(dct["@date"]).date()
  else:
    return dct


def to_json(dct, pretty=False, sort_keys=False):
  """
  Opposite of parse_json.
  Converts a :any`_Expr` into a request body, calling :any:`to_fauna_json`.
  """
  if pretty:
    return dumps(dct, cls=_FaunaJSONEncoder, sort_keys=True, indent=2, separators=(", ", ": "))
  else:
    return dumps(dct, cls=_FaunaJSONEncoder, sort_keys=sort_keys, separators=(",", ":"))


def _datetime_to_str(value):
  if value.utcoffset() is None:
    raise ValueError("Fauna time requires offset-aware datetimes")

  return value.isoformat().replace("+00:00", "Z")


class _FaunaJSONEncoder(JSONEncoder):
  """Converts :any:`_Expr`, :any:`datetime`, :any:`date` to JSON."""
  # pylint: disable=method-hidden
  def default(self, obj):
    if isinstance(obj, _Expr):
      return obj.to_fauna_json()
    elif isinstance(obj, datetime):
      return {"@ts": _datetime_to_str(obj)}
    elif isinstance(obj, date):
      return {"@date": obj.isoformat()}
    else:
      return obj
