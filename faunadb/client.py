from time import time
# pylint: disable=redefined-builtin
from builtins import object
import threading

from requests import Request, Session
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter

from faunadb.errors import _get_or_raise, FaunaError, UnexpectedError
from faunadb.query import _wrap
from faunadb.request_result import RequestResult
from faunadb._json import parse_json_or_none, to_json

API_VERSION = "2.7"

class _LastTxnTime(object):
  """Wraps tracking the last transaction time supplied from the database."""
  def __init__(self):
    self._lock = threading.Lock()
    self._time = None

  @property
  def time(self):
    """Produces the last transaction time, or, None if not yet updated."""
    with self._lock:
      return self._time

  @property
  def request_header(self):
    """Produces a dictionary with a non-zero `X-Last-Txn-Time` header; or,
    if one has not yet been set, the empty header dictionary."""
    t = self.time
    if t is None:
      return {}
    return { "X-Last-Txn-Time" : str(t) }

  def update_txn_time(self, new_txn_time):
      """Updates the internal transaction time.
      In order to maintain a monotonically-increasing value, `newTxnTime`
      is discarded if it is behind the current timestamp."""
      with self._lock:
          if self._time is None:
              self._time = new_txn_time
          else:
              self._time = max(self._time, new_txn_time)

class _Counter(object):
  def __init__(self, init_value=0):
    self.lock = threading.Lock()
    self.counter = init_value

  def __str__(self):
    return "Counter(%s)" % self.counter

  def get_and_increment(self):
    with self.lock:
      counter = self.counter
      self.counter += 1
      return counter

  def decrement(self):
    with self.lock:
      self.counter -= 1
      return self.counter

class FaunaClient(object):
  """
  Directly communicates with FaunaDB via JSON.

  For data sent to the server, the ``to_fauna_json`` method will be called on any values.
  It is encouraged to pass e.g. :any:`Ref` objects instead of raw JSON data.

  All methods return a converted JSON response.
  This is a dict containing lists, ints, floats, strings, and other dicts.
  Any :any:`Ref`, :any:`SetRef`, :any:`FaunaTime`, or :class:`datetime.date`
  values in it will also be parsed.
  (So instead of ``{"@ref": {"id": "frogs", "class": {"@ref": {"id": "classes"}}}}``,
  you will get ``Ref("frogs", Native.CLASSES)``.)
  """

  # pylint: disable=too-many-arguments, too-many-instance-attributes
  def __init__(
      self,
      secret,
      domain="db.fauna.com",
      scheme="https",
      port=None,
      timeout=60,
      observer=None,
      pool_connections=10,
      pool_maxsize=10,
      **kwargs):
    """
    :param secret:
      Auth token for the FaunaDB server.
    :param domain:
      Base URL for the FaunaDB server.
    :param scheme:
      ``"http"`` or ``"https"``.
    :param port:
      Port of the FaunaDB server.
    :param timeout:
      Read timeout in seconds.
    :param observer:
      Callback that will be passed a :any:`RequestResult` after every completed request.
    :param pool_connections:
      The number of connection pools to cache.
    :param pool_maxsize:
      The maximum number of connections to save in the pool.
    """

    self.domain = domain
    self.scheme = scheme
    self.port = (443 if scheme == "https" else 80) if port is None else port

    self.auth = HTTPBasicAuth(secret, "")
    self.base_url = "%s://%s:%s" % (self.scheme, self.domain, self.port)
    self.observer = observer

    self.pool_connections = pool_connections
    self.pool_maxsize = pool_maxsize

    self._last_txn_time = kwargs.get('last_txn_time') or _LastTxnTime()

    if ('session' not in kwargs) or ('counter' not in kwargs):
      self.session = Session()
      self.session.mount('https://', HTTPAdapter(pool_connections=pool_connections,
                                                 pool_maxsize=pool_maxsize))
      self.session.mount('http://', HTTPAdapter(pool_connections=pool_connections,
                                                pool_maxsize=pool_maxsize))
      self.counter = _Counter(1)

      self.session.headers.update({
        "Accept-Encoding": "gzip",
        "Content-Type": "application/json;charset=utf-8",
        "X-Fauna-Driver": "python",
        "X-FaunaDB-API-Version": API_VERSION
      })
      self.session.timeout = timeout
    else:
      self.session = kwargs['session']
      self.counter = kwargs['counter']

  def sync_last_txn_time(self, new_txn_time):
    """
    Sync the freshest timestamp seen by this client.

    This has no effect if staler than currently stored timestamp.
    WARNING: This should be used only when coordinating timestamps across
            multiple clients. Moving the timestamp arbitrarily forward into
            the future will cause transactions to stall.
    
    :param new_txn_time: the new seen transaction time.
    """
    self._last_txn_time.update_txn_time(new_txn_time)

  def get_last_txn_time(self):
    """
    Get the freshest timestamp reported to this client.
    :return:
    """
    return self._last_txn_time.time

  def __del__(self):
    if self.counter.decrement() == 0:
      self.session.close()

  def query(self, expression):
    """
    Use the FaunaDB query API.

    :param expression: A query. See :doc:`query` for information on queries.
    :return: Converted JSON response.
    """
    return self._execute("POST", "", _wrap(expression), with_txn_time=True)

  def ping(self, scope=None, timeout=None):
    """
    Ping FaunaDB.
    """
    return self._execute("GET", "ping", query={"scope": scope, "timeout": timeout})

  def new_session_client(self, secret, observer=None):
    """
    Create a new client from the existing config with a given secret.
    The returned client share its parent underlying resources.

    :param secret:
      Credentials to use when sending requests.
    :param observer:
      Callback that will be passed a :any:`RequestResult` after every completed request.
    :return:
    """
    if self.counter.get_and_increment() > 0:
      return FaunaClient(secret=secret,
                         domain=self.domain,
                         scheme=self.scheme,
                         port=self.port,
                         timeout=self.session.timeout,
                         observer=observer or self.observer,
                         session=self.session,
                         counter=self.counter,
                         pool_connections=self.pool_connections,
                         pool_maxsize=self.pool_maxsize,
                         last_txn_time=self._last_txn_time)
    else:
      raise UnexpectedError("Cannnot create a session client from a closed session", None)

  def _execute(self, action, path, data=None, query=None, with_txn_time=False):
    """Performs an HTTP action, logs it, and looks for errors."""
    if query is not None:
      query = {k: v for k, v in query.items() if v is not None}

    headers = {}

    if with_txn_time:
        headers.update(self._last_txn_time.request_header)

    start_time = time()
    response = self._perform_request(action, path, data, query, headers)
    end_time = time()

    if with_txn_time:
      if "X-Txn-Time" in response.headers:
        new_txn_time = int(response.headers["X-Txn-Time"])
        self.sync_last_txn_time(new_txn_time)

    response_raw = response.text
    response_content = parse_json_or_none(response_raw)

    request_result = RequestResult(
      action, path, query, data,
      response_raw, response_content, response.status_code, response.headers,
      start_time, end_time)

    if self.observer is not None:
      self.observer(request_result)

    if response_content is None:
      raise UnexpectedError("Invalid JSON.", request_result)

    FaunaError.raise_for_status_code(request_result)
    return _get_or_raise(request_result, response_content, "resource")

  def _perform_request(self, action, path, data, query, headers):
    """Performs an HTTP action."""
    url = self.base_url + "/" + path
    req = Request(action, url, params=query, data=to_json(data), auth=self.auth, headers=headers)
    return self.session.send(self.session.prepare_request(req))
