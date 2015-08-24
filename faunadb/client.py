from logging import getLogger
from os import environ
from time import time

from requests import codes, Request, Session

from .errors import BadRequest, FaunaHTTPError, InternalError, MethodNotAllowed, NotFound,\
  PermissionDenied, Unauthorized, UnavailableError
from .objects import Ref
from ._json import parse_json, to_json, to_json_pretty
from ._util import Spreader

class Client(object):
  """
  Communicates directly with FaunaDB.
  For a more structured approach, see various methods on Model that use a Client.

  Methods return responses converted from JSON to dicts.
  The types in faunadb.objects will be converted from JSON as well,
  so instead of returning { "@ref": "users/123" } you will get a Ref("users/123").

  Response dict will also have "headers" containing HTTP headers of the response.
  """

  # pylint: disable=too-many-arguments, too-many-instance-attributes
  def __init__(
      self,
      logger=None,
      domain="rest.faunadb.com",
      scheme="https",
      port=None,
      timeout=60,
      secret=None,
      api_version=None):
    """
    :param logger:
      A Logger object.
      Will be called to log every request and response.
    :param domain:
      Base URL for the FaunaDB server.
    :param scheme:
      "http" or "https".
    :param port:
      Port for the FaunaDB server.
    :param timeout:
      Number of seconds after which requests are considered failed.
    :param secret:
      Auth token for the FaunaDB server.
    """

    self.logger = logger
    self.domain = domain
    self.scheme = scheme
    self.api_version = api_version
    self.port = (443 if scheme == "https" else 80) if port is None else port

    if environ.get("FAUNA_DEBUG"):
      logger = getLogger(__name__)
      self.logger = logger if self.logger is None else Spreader([self.logger, logger])

    self.session = Session()
    if secret is not None:
      self.session.auth = self.credentials = Client._credentials_from_string(secret)

    self.session.headers.update({
      "Accept-Encoding": "gzip",
      "Content-Type": "application/json;charset=utf-8"
    })
    self.session.timeout = timeout

    self.base_url = "%s://%s:%s" % (self.scheme, self.domain, self.port)

  def get(self, path, query=None):
    """
    HTTP GET. See https://faunadb.com/documentation#rest.

    :param path: Path relative to self.domain. May be a Ref.
    :param query: Dict to be converted to URL parameters.
    :return: Response.
    """
    return self._execute("GET", path, query=query or {})

  def post(self, path, data=None):
    """
    HTTP POST. See https://faunadb.com/documentation#rest.
    :param path: Path relative to self.domain. May be a Ref.
    :param data: Dict to be converted to request JSON. May contain types in faunadb.objects.
    :return: Response.
    """
    return self._execute("POST", path, data or {})

  def put(self, path, data=None):
    """Like Client.post, but a PUT request."""
    return self._execute("PUT", path, data or {})

  def patch(self, path, data=None):
    """Like Client.post, but a PATCH request. See https://faunadb.com/documentation#rest."""
    return self._execute("PATCH", path, data or {})

  def delete(self, path, data=None):
    """Like Client.delete, but a DELETE request.  See https://faunadb.com/documentation#rest."""
    return self._execute("DELETE", path, data or {})

  def query(self, expression):
    """
    Use the FaunaDB query API. See https://faunadb.com/documentation#queries.

    :param expression: Dict generated by functions in faunadb.query.
    :return: Response.
    """
    return self._execute("POST", "", expression)

  def ping(self, scope=None, timeout=None):
    """Ping the server. See https://faunadb.com/documentation#rest-other."""
    return self.get('ping', {"scope": scope, "timeout": timeout})

  def _log(self, indent, logged):
    """Indents `logged` before sending it to self.logger."""
    indent_str = ' ' * indent
    logged = indent_str + ("\n" + indent_str).join(logged.split("\n"))
    self.logger.debug(logged)

  def _execute(self, action, path, data=None, query=None):
    """Performs an HTTP action, logs it, and looks for errors."""
    # pylint: disable=too-many-branches

    if isinstance(path, Ref):
      path = str(path)
    if query is not None:
      query = {k: v for k, v in query.iteritems() if v is not None}

    # pylint: disable=too-many-branches
    if self.logger is not None:
      self._log(0, "Fauna %s /%s%s" % (
        action.upper(),
        path,
        Client._query_string_for_logging(query)))
      if hasattr(self, "credentials"):
        self._log(2, "Credentials: %s:%s" % self.credentials)
      if data:
        self._log(2, "Request JSON: %s" % to_json_pretty(data))

      real_time_begin = time()
      response = self._execute_without_logging(action, path, data, query)
      real_time_end = time()
      real_time = real_time_end - real_time_begin

      # headers is initially a CaseInsensitiveDict, which can't be converted to JSON
      headers_json = to_json_pretty(dict(response.headers))
      response_dict = parse_json(response.text)
      response_json = to_json_pretty(response_dict)
      self._log(2, "Response headers: %s" % headers_json)
      self._log(2, "Response JSON: %s" % response_json)
      self._log(
        2,
        "Response (%i): API processing %sms, network latency %ims" % (
          response.status_code,
          response.headers["X-HTTP-Request-Processing-Time"],
          int(real_time * 1000)))
      return Client._handle_response(response, response_dict)
    else:
      response = self._execute_without_logging(action, path, data, query)
      response_dict = parse_json(response.text)
      return Client._handle_response(response, response_dict)

  def _execute_without_logging(self, action, path, data, query):
    """Performs an HTTP action."""
    url = self.base_url + "/" + path
    headers = {"x-faunadb-api-version": self.api_version} if self.api_version else None
    req = Request(action, url, headers=headers, params=query, data=to_json(data))
    return self.session.send(self.session.prepare_request(req))

  @staticmethod
  def _handle_response(response, response_dict):
    """Looks for error codes in response. If not, parses it."""
    # pylint: disable=no-member
    code = response.status_code
    if 200 <= code <= 299:
      return Response.from_requests_response(response.headers, response_dict)
    elif code == codes.bad_request:
      raise BadRequest(response)
    elif code == codes.unauthorized:
      raise Unauthorized(response)
    elif code == codes.forbidden:
      raise PermissionDenied(response)
    elif code == codes.not_found:
      raise NotFound(response)
    elif code == codes.method_not_allowed:
      raise MethodNotAllowed(response)
    elif code == codes.internal_server_error:
      raise InternalError(response)
    elif code == codes.unavailable:
      raise UnavailableError(response)
    else:
      raise FaunaHTTPError(response)

  @staticmethod
  def _query_string_for_logging(query):
    """Converts a query dict to URL params."""
    if not query:
      return ""
    return "?" + "&".join(("%s=%s" % (k, v) for k, v in query.iteritems()))

  # user:pass -> (user, pass)
  @staticmethod
  def _credentials_from_string(secret):
    """Converts a username:password string to (username, password)."""
    pair = secret.split(":", 1)
    if len(pair) == 1:
      pair.append('')
    return tuple(pair)


class Response(object):
  """
  Return type of most Client methods.
  """

  @staticmethod
  def from_requests_response(response_headers, response_dict):
    """Creates a Response from the response returned by the `requests` module."""
    return Response(response_dict["resource"], response_headers)

  def __init__(self, resource, headers):
    self.resource = resource
    """
    The converted JSON response.
    This is a dict whose members may have been converted to the types in faunadb.objects.
    """
    self.headers = headers
    """Dict of HTTP headers. See See https://faunadb.com/documentation#guide-protocol."""
