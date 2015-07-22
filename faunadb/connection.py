from logging import getLogger
from os import environ
from time import time

from requests import codes, Request, Session

from .errors import BadRequest, FaunaHTTPError, InternalError, MethodNotAllowed, NotFound,\
  PermissionDenied, Unauthorized, UnavailableError
from ._json import to_json, to_json_pretty
from ._util import Spreader


class Connection(object):
  """
  Stores info for communicating with a FaunaDB server.
  Generally, you will not have to deal with this directly after constructing it.
  Instead, use a Client.
  """
  # pylint: disable=too-many-arguments
  def __init__(
      self,
      logger=None,
      domain="rest.faunadb.com",
      scheme="https",
      port=None,
      timeout=60,
      secret=None):
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
    self.port = (443 if scheme == "https" else 80) if port is None else port

    if environ.get("FAUNA_DEBUG"):
      logger = getLogger(__name__)
      self.logger = logger if self.logger is None else Spreader([self.logger, logger])

    self.session = Session()
    if secret is not None:
      self.session.auth = self.credentials = Connection._credentials_from_string(secret)

    self.session.headers.update({
      "Accept-Encoding": "gzip",
      "Content-Type": "application/json;charset=utf-8"
    })
    self.session.timeout = timeout

    self.base_url = "%s://%s:%s" % (self.scheme, self.domain, self.port)

  def get(self, path, query=None):
    """
    :param path: Path relative to the self.domain.
    :param query: Hash to be converted to URL parameters.
    :return: (response, headers)
    """
    return self._execute("GET", path, query=query or {})

  def post(self, path, data=None):
    """
    :param path: Path relative to self.domain.
    :param data: Dict to be converted to a JSON body.
    :return: (response, headers)
    """
    return self._execute("POST", path, data or {})

  def put(self, path, data=None):
    """Like Connection.post, but is a PUT."""
    return self._execute("PUT", path, data or {})

  def patch(self, path, data=None):
    """Like Connection.post, but is a PATCH."""
    return self._execute("PATCH", path, data or {})

  def delete(self, path, data=None):
    """Like Connection.post, but is a DELETE."""
    return self._execute("DELETE", path, data or {})

  def _log(self, indent, logged):
    """Indents `logged` before sending it to self.logger."""
    for line in logged.split('\n'):
      print line
      self.logger.debug(' ' * indent + line)

  def _execute(self, action, path, data=None, query=None):
    """Performs an HTTP action, logs it, and looks for errors."""
    # pylint: disable=too-many-branches
    if self.logger is not None:
      self._log(0, "Fauna %s /%s%s" % (
        action.upper(),
        path,
        Connection._query_string_for_logging(query)))
      if hasattr(self, "credentials"):
        self._log(2, "Credentials: %s:%s" % self.credentials)
      if data:
        self._log(2, "Request JSON: %s" % to_json_pretty(data))

      real_time_begin = time()
      response = self._execute_without_logging(action, path, data, query)
      real_time_end = time()

      real_time = real_time_end - real_time_begin
      cpu_time = 0 # TODO: difference in process_time
      # time.process_time() new in python 3.3, so can't use that yet.
      # https://docs.python.org/3.3/library/time.html#time.process_time
      latency_time = real_time - cpu_time

      # headers is initially a CaseInsensitiveDict, which can't be converted to JSON
      headers_json = to_json_pretty(dict(response.headers))
      self._log(2, "Response headers, %s\nResponse JSON: %s" % (headers_json, response.text))
      self._log(
        2,
        "Response (%i): API processing %sms, network latency %ims, local processing %ims" % (
          response.status_code,
          response.headers["X-HTTP-Request-Processing-Time"],
          int(latency_time * 1000),
          int(cpu_time * 1000)))
    else:
      response = self._execute_without_logging(action, path, data, query)

    # pylint: disable=no-member
    code = response.status_code
    if 200 <= code <= 299:
      return (response.text, response.headers)
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

  def _execute_without_logging(self, action, path, data, query):
    """Performs an HTTP action."""
    url = self.base_url + "/" + path
    req = Request(action, url, params=query, data=to_json(data))
    return self.session.send(self.session.prepare_request(req))

  @staticmethod
  def _query_string_for_logging(query):
    """Converts a query dict to URL params."""
    if not query:
      return ""
    return "?" + "&".join((k + "=" + v for k, v in query.iteritems()))

  # user:pass -> (user, pass)
  @staticmethod
  def _credentials_from_string(secret):
    """Converts a username:password string to (username, password)."""
    pair = secret.split(":", 1)
    if len(pair) == 1:
      pair.append('')
    return tuple(pair)
