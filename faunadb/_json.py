from datetime import date, datetime
from iso8601 import parse_date
from json import dumps, loads, JSONEncoder

from .errors import InvalidResponse
from .objects import FaunaTime, Ref, Set


def parse_json(json_string):
  """
  Parses a JSON string into python values.
  Also parses :any:`Ref`, :any:`Set`, :any:`FaunaTime`, and :class:`date`.
  """
  try:
    return loads(json_string, object_hook=_parse_json_hook)
  except ValueError:
    raise InvalidResponse("Bad json: %s" % json_string)


def _parse_json_hook(dct):
  """
  Looks for FaunaDB types in a JSON object and converts to them if possible.
  """
  if "@ref" in dct:
    return Ref(dct["@ref"])
  if "@obj" in dct:
    return dct["@obj"]
  if "@set" in dct:
    return Set(dct["@set"])
  if "@ts" in dct:
    return FaunaTime(dct["@ts"])
  if "@date" in dct:
    return parse_date(dct["@date"]).date()
  else:
    return dct


def to_json(dct, pretty=False):
  """
  Opposite of parse_json.
  Converts a dict into a request body, calling :any:`to_fauna_json`.
  """
  if pretty:
    return dumps(dct, cls=_FaunaJSONEncoder, sort_keys=True, indent=2, separators=(", ", ": "))
  else:
    return dumps(dct, cls=_FaunaJSONEncoder, separators=(",", ":"))


class _FaunaJSONEncoder(JSONEncoder):
  """Converts values with :any:`to_fauna_json` to JSON."""
  # pylint: disable=method-hidden
  def default(self, obj):
    if hasattr(obj, "to_fauna_json"):
      return self._to_fauna_json_recursive(obj)
    elif isinstance(obj, datetime):
      return FaunaTime(obj).to_fauna_json()
    elif isinstance(obj, date):
      return {"@date": obj.isoformat()}
    else:
      return obj

  def _to_fauna_json_recursive(self, obj):
    """
    Calls to_fauna on obj if possible.
    Recursively calls .to_fauna() on the results of that too.
    This ensures that values implementing to_fauna don't need to call it recursively themselves.
    """
    dct = obj.to_fauna_json()
    return {k: self.default(v) for k, v in dct.iteritems()}
