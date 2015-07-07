from collections import namedtuple

from faunadb.errors import InvalidQuery
from faunadb._json import parse_json

class Client(object):
  """
  Wraps a Connection with FaunaDB logic.
  Use this instead of Connection!

  Methods return responses converted from JSON to dicts.
  The types in faunadb.objects will be converted from JSON as well,
  so instead of returning { "@ref": "users/123" } you will get a Ref("users/123").

  Response dict will also have "headers" containing HTTP headers of the response.
  """

  def __init__(self, connection):
    self.connection = connection

  def get(self, path, query=None, pagination=None):
    """
    HTTP GET.

    :param path: Path relative to connection.domain. May be a Ref.
    :param query: Dict to be converted to URL parameters.
    :param pagination:
    :return: Response dict.
    """

    return self.get_with_headers(path, query, pagination).response

  def get_with_headers(self, path, query=None, pagination=None):
    query = (query or {})
    if pagination is not None:
      query.update(pagination)
    return _resource_and_headers(self.connection.get(str(path), query))

  def post(self, path, data=None):
    """
    HTTP POST.
    :param path:
      Path relative to connection.domain. May be a Ref.
    :param data:
      Dict to be converted to request JSON.
      May contain types in faunadb.objects)
    :return: Response dict.
    """

    return _just_resource(self.connection.post(str(path), data))

  def post_with_headers(self, path, data=None):
    return _resource_and_headers(self.connection.post(str(path), data))

  def put(self, path, data=None):
    "Like Client.post, but a PUT request."
    return _just_resource(self.connection.put(str(path), data))

  def put_with_headers(self, path, data=None):
    return _resource_and_headers(self.connection.put(str(path), data))

  def patch(self, path, data=None):
    "Like Client.post, but a PATCH request."
    return _just_resource(self.connection.patch(str(path), data))
  def patch_with_headers(self, path, data=None):
    return _resource_and_headers(self.connection.patch(str(path), data))

  def delete(self, path, data=None):
    "Like Client.delete, but a DELETE request. Returns headers."
    return self.connection.delete(str(path), data)

  # For using the query API instead of REST.
  def query(self, expression):
    """
    :param query: Dict generated by functions in faunadb.query.
    :return: Response dict.
    """

    def quote():
      params = expression["params"]
      if "object" in params:
        raise InvalidQuery("%s does not support object, use quote")
      return params["quote"]

    for method in ["get", "create", "update", "replace", "delete"]:
      ref = expression.get(method)
      if ref:
        if ref.to_class() in ["databases", "keys"]:
          if method == "get":
            return self.get(ref, {"ts": expression["ts"]})
          elif method == "create":
            return self.post(ref, quote())
          elif method == "update":
            return self.patch(ref, quote())
          elif method == "replace":
            return self.put(ref, quote())
          elif method == "delete":
            return self.delete(ref)

    return self.post("", expression)


ResponseWithHeaders = namedtuple("ResponseWithHeaders", ["response", "headers"])


def _just_resource(body_headers):
  'Convert response JSON to a dict with "headers".'
  return _resource(body_headers[0])

def _resource_and_headers(body_headers):
  body, headers = body_headers
  return ResponseWithHeaders(_resource(body), headers)

def _resource(body):
  dct = parse_json(body)
  assert len(dct) == 1
  return dct["resource"]

