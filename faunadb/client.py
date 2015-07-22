from .errors import InvalidQuery
from ._json import parse_json


class Client(object):
  """
  Main class for communicating directly with FaunaDB.
  For a more structured approach, see various methods on Model that use a Client.

  Methods return responses converted from JSON to dicts.
  The types in faunadb.objects will be converted from JSON as well,
  so instead of returning { "@ref": "users/123" } you will get a Ref("users/123").

  Response dict will also have "headers" containing HTTP headers of the response.
  """

  def __init__(self, connection):
    self.connection = connection

  #region REST
  def get(self, path, query=None):
    """
    HTTP GET. See https://faunadb.com/documentation#rest.

    :param path: Path relative to connection.domain. May be a Ref.
    :param query: Dict to be converted to URL parameters.
    :return: Response.
    """
    return Response.from_connection_response(self.connection.get(str(path), query))

  def post(self, path, data=None):
    """
    HTTP POST. See https://faunadb.com/documentation#rest.
    :param path: Path relative to connection.domain. May be a Ref.
    :param data: Dict to be converted to request JSON. May contain types in faunadb.objects.
    :return: Response dict.
    """
    return Response.from_connection_response(self.connection.post(str(path), data))

  def put(self, path, data=None):
    """Like Client.post, but a PUT request."""
    return Response.from_connection_response(self.connection.put(str(path), data))

  def patch(self, path, data=None):
    """Like Client.post, but a PATCH request. See https://faunadb.com/documentation#rest."""
    return Response.from_connection_response(self.connection.patch(str(path), data))

  def delete(self, path, data=None):
    """Like Client.delete, but a DELETE request.  See https://faunadb.com/documentation#rest."""
    return Response.from_connection_response(self.connection.delete(str(path), data))
  #endregion

  def query(self, expression):
    """
    Use the FaunaDB query API. See https://faunadb.com/documentation#queries.

    :param query: Dict generated by functions in faunadb.query.
    :return: Response.
    """

    for method in ["get", "create", "update", "replace", "delete"]:
      ref = expression.get(method)
      if ref:
        if str(ref.to_class()) in ("databases", "keys"):
          def get_quote():
            """Get the "quote" value from params."""
            params = expression["params"]
            if "object" in params:
              # pylint: disable=cell-var-from-loop
              raise InvalidQuery(
                "%s does not support query.object, use query.quote instead." % method)
            return params["quote"]

          if method == "get":
            return self.get(ref, {"ts": expression["ts"]})
          elif method == "create":
            return self.post(ref, get_quote())
          elif method == "update":
            return self.patch(ref, get_quote())
          elif method == "replace":
            return self.put(ref, get_quote())
          else:
            return self.delete(ref)

    return self.post("", expression)


class Response(object):
  """
  Both a JSON response body and the HTTP headers that came with it.
  Headers contain metadata that may be useful.
  See faunadb.com/documentation#guide-protocol
  """

  @staticmethod
  def from_connection_response(body_headers):
    "Parses the body of the response."
    body, headers = body_headers
    resource = parse_json(body)["resource"]
    return Response(resource, headers)

  def __init__(self, resource, headers):
    """Create a new ResponseWithHeaders."""
    self.resource = resource
    """The converted JSON response."""
    self.headers = headers
    """Dict of HTTP headers."""
