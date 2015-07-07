"Functions for converting to and from JSON using types in faunadb.objects."

from json import dumps, loads, JSONEncoder

from faunadb.objects import Ref, Set, Obj, Event

def parse_json(json_string):
  "Parses a JSON string into a dict containing types from faunadb.objects."
  return loads(json_string, object_hook=_parse_json_hook)


def _parse_json_hook(dct):
  "Looks for FaunaDB types in a JSON object and converts to them if possible."
  if "@ref" in dct:
    assert len(dct) == 1
    return Ref(dct["@ref"])
  if "@obj" in dct:
    assert len(dct) == 1
    return Obj(**dct["@obj"])
  if "@set" in dct:
    assert len(dct) == 1
    dct = dct["@set"]
    assert len(dct) == 2
    return Set(dct["match"], dct["index"])
  #if "ts" in dct and "action" in dct and "resource" in dct:
  #  assert len(dct) == 3
  #  return Event(dct["ts"], dct["action"], dct["resource"])
  return dct


def to_json(dct, **opts):
  """
  Opposite of parse_json.
  Converts a dict, possibly containing types from faunadb.objects, into a request body.
  """
  return dumps(dct, cls=_FaunaJSONEncoder, **opts)


def to_json_pretty(dct):
  "to_json with indentation."
  return to_json(dct, sort_keys=True, indent=2, separators=(',', ': '))


class _FaunaJSONEncoder(JSONEncoder):
  "Converts FaunaDB objects to JSON."

  # pylint: disable=method-hidden
  def default(self, obj):
    if isinstance(obj, Ref):
      return {"@ref": obj.ref_str}
    if isinstance(obj, Set):
      return {"@set": {"match": obj.match, "index": obj.index}}
    if isinstance(obj, Obj):
      return {"object": obj.dct}
    if isinstance(obj, Event):
      dct = {"ts": obj.ts, "action": obj.action, "resource": obj.resource}
      return {k: v for k, v in dct.iteritems() if v is not None}
    else:
      return JSONEncoder.default(self, obj)
