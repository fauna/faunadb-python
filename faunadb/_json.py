from base64 import decode, urlsafe_b64decode, urlsafe_b64encode
from datetime import date, datetime
from json import JSONEncoder, dumps, loads

from iso8601 import parse_date

from faunadb.errors import UnexpectedError
from faunadb.objects import FaunaTime, Native, Query, Ref, SetRef
from faunadb.query import _Expr


def parse_json(json_string):
    """
    Parses a JSON string into python values.
    Also parses :any:`Ref`, :any:`SetRef`, :any:`FaunaTime`, and :class:`date`.
    """
    return loads(json_string, object_hook=_parse_json_hook)


def parse_json_or_none(json_string):
    try:
        return parse_json(json_string)
    except ValueError:
        return None


def _parse_json_hook(dct):
    # pylint: disable=too-many-return-statements
    """
    Looks for FaunaDB types in a JSON object and converts to them if possible.
    """
    if "@ref" in dct:
        ref = dct["@ref"]

        if (not "collection" in ref) and (not "database" in ref):
            return Native.from_name(ref["id"])

        return Ref(ref["id"], ref.get("collection"), ref.get("database"))
    if "@obj" in dct:
        return dct["@obj"]
    if "@set" in dct:
        return SetRef(dct["@set"])
    if "@query" in dct:
        return Query(dct["@query"])
    if "@ts" in dct:
        return FaunaTime(dct["@ts"])
    if "@date" in dct:
        return parse_date(dct["@date"]).date()
    if "@bytes" in dct:
        return bytearray(urlsafe_b64decode(dct["@bytes"].encode()))
    return dct


def to_json(dct, pretty=False, sort_keys=False):
    """
    Opposite of parse_json.
    Converts a :any`_Expr` into a request body, calling :any:`to_fauna_json`.
    """
    if pretty:
        return dumps(dct, cls=_FaunaJSONEncoder, sort_keys=True, indent=2, separators=(", ", ": "))
    return dumps(dct, cls=_FaunaJSONEncoder, sort_keys=sort_keys, separators=(",", ":"))


def stream_content_to_json(buffer):
    values = []

    try:
        content = parse_json(buffer)
        values.append({"content": content, "raw": buffer})
        buffer = ''
    except Exception:
        while True:
            pos = buffer.find("\n") + 1
            if (pos <= 0):
                break
            slice = buffer[0:pos].strip()
            if (len(pos) > 0):
                # discards empty slices due to leading \n
                values.append({"content": slice.decode(), "raw": slice})
                buffer = buffer[pos].encode()

    return {"buffer": buffer,  "values": values}


class _FaunaJSONEncoder(JSONEncoder):
    """Converts :any:`_Expr`, :any:`datetime`, :any:`date` to JSON."""
    # pylint: disable=method-hidden,arguments-differ

    def default(self, obj):
        if isinstance(obj, _Expr):
            return obj.to_fauna_json()
        elif isinstance(obj, datetime):
            return FaunaTime(obj).to_fauna_json()
        elif isinstance(obj, date):
            return {"@date": obj.isoformat()}
        elif isinstance(obj, (bytes, bytearray)):
            return {"@bytes": urlsafe_b64encode(obj).decode('utf-8')}
        else:
            raise UnexpectedError(
                "Unserializable object {} of type {}".format(obj, type(obj)), None)
