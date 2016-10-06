from time import time
# pylint: disable=redefined-builtin
from builtins import object

from requests import Request, Session

from faunadb.errors import FaunaError, UnexpectedError
from faunadb.objects import Ref
from faunadb.query import _wrap
from faunadb.request_result import RequestResult
from faunadb._json import parse_json_or_none, to_json


class Client(object):
  """
  Directly communicates with FaunaDB via JSON.

  For data sent to the server, the ``to_fauna_json`` method will be called on any values.
  It is encouraged to pass e.g. :any:`Ref` objects instead of raw JSON data.

  All methods return a converted JSON response.
  This is a dict containing lists, ints, floats, strings, and other dicts.
  Any :any:`Ref`, :any:`SetRef`, :any:`FaunaTime`, or :class:`datetime.date`
  values in it will also be parsed.
  (So instead of ``{ "@ref": "classes/frogs/123" }``, you will get ``Ref("classes/frogs", "123")``.)
  """

  # pylint: disable=too-many-arguments, too-many-instance-attributes
  def __init__(
      self,
      domain="rest.faunadb.com",
      scheme="https",
      port=None,
      timeout=60,
      secret=None,
      observer=None):
    """
    :param domain:
      Base URL for the FaunaDB server.
    :param scheme:
      ``"http"`` or ``"https"``.
    :param port:
      Port of the FaunaDB server.
    :param timeout:
      Read timeout in seconds.
    :param secret:
      Auth token for the FaunaDB server.
      Should resemble "username", "username:password", or ("username", "password").
    :param observer:
      Callback that will be passed a :any:`RequestResult` after every completed request.
    """

    self.domain = domain
    self.scheme = scheme
    self.port = (443 if scheme == "https" else 80) if port is None else port

    self.session = Session()
    if secret is not None:
      self.session.auth = Client._parse_secret(secret)

    self.session.headers.update({
      "Accept-Encoding": "gzip",
      "Content-Type": "application/json;charset=utf-8"
    })
    self.session.timeout = timeout

    self.base_url = "%s://%s:%s" % (self.scheme, self.domain, self.port)

    self.observer = observer

  def __del__(self):
    # pylint: disable=bare-except
    try:
      self.session.close()
    except:
      pass

  def query(self, expression):
    """
    Use the FaunaDB query API.

    :param expression: A query. See :doc:query for information on queries.
    :return: Converted JSON response.
    """
    return self._execute("POST", "", _wrap(expression))

  def ping(self, scope=None, timeout=None):
    """
    Ping FaunaDB.
    See the `docs <https://fauna.com/documentation/rest#other>`__.
    """
    return self._execute("GET", "ping", query={"scope": scope, "timeout": timeout})

  def _execute(self, action, path, data=None, query=None):
    """Performs an HTTP action, logs it, and looks for errors."""
    # pylint: disable=raising-bad-type
    if isinstance(path, Ref):
      path = path.value

    if query is not None:
      query = {k: v for k, v in query.items() if v is not None}

    start_time = time()
    response = self._perform_request(action, path, data, query)
    end_time = time()
    response_raw = response.text
    response_content = parse_json_or_none(response_raw)

    request_result = RequestResult(
      self,
      action, path, query, data,
      response_raw, response_content, response.status_code, response.headers,
      start_time, end_time)

    if self.observer is not None:
      self.observer(request_result)

    if response_content is None:
      raise UnexpectedError("Invalid JSON.", request_result)

    FaunaError.raise_for_status_code(request_result)
    return UnexpectedError.get_or_raise(request_result, response_content, "resource")

  def _perform_request(self, action, path, data, query):
    """Performs an HTTP action."""
    url = self.base_url + "/" + path
    req = Request(action, url, params=query, data=to_json(data))
    return self.session.send(self.session.prepare_request(req))

  @staticmethod
  def _parse_secret(secret):
    if isinstance(secret, tuple):
      if len(secret) != 2:
        raise ValueError("Secret tuple must have exactly two entries")
      return secret
    else:
      pair = secret.split(":", 1)
      if len(pair) == 1:
        pair.append("")
      return tuple(pair)
