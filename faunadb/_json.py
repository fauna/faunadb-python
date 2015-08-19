"Functions for converting to and from JSON using types in faunadb.objects."

from json import dumps, loads, JSONEncoder

from .objects import Ref, Set


def parse_json(json_string):
  """
  Parses a JSON string into a dict containing types from faunadb.objects.
  """
  return loads(json_string, object_hook=_parse_json_hook)


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
  else:
    return dct


def to_json(dct, **opts):
  """
  Opposite of parse_json.
  Converts a dict, possibly containing types from faunadb.objects, into a request body.
  """
  return dumps(dct, cls=_FaunaJSONEncoder, **opts)


def to_json_pretty(dct):
  """to_json with indentation."""
  return to_json(dct, sort_keys=True, indent=2, separators=(',', ': '))


class _FaunaJSONEncoder(JSONEncoder):
  """Converts FaunaDB objects to JSON."""
  # pylint: disable=method-hidden
  def default(self, obj):
    if hasattr(obj, "to_fauna_json"):
      return _FaunaJSONEncoder._to_fauna_json_recursive(obj)
    else:
      return JSONEncoder.default(self, obj)

  @staticmethod
  def _to_fauna_json_recursive(obj):
    """
    Calls to_fauna on obj if possible.
    Recursively calls .to_fauna() on the results of that too.
    This ensures that objects implementing to_fauna don't need to call it recursively theirselves.
    """
    dct = obj.to_fauna_json()
    for key, value in dct.iteritems():
      if hasattr(value, "to_fauna_json"):
        dct[key] = _FaunaJSONEncoder._to_fauna_json_recursive(value)
    return dct
