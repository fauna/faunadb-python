import os
import platform
import re
import sys
import threading
# pylint: disable=redefined-builtin
from builtins import object
from time import time

from requests import Request, Session, get
from requests.adapters import HTTPAdapter
from requests.auth import AuthBase

from faunadb import __api_version__ as api_version
from faunadb import __version__ as pkg_version
from faunadb._json import parse_json_or_none, to_json
from faunadb.errors import FaunaError, UnexpectedError, _get_or_raise
from faunadb.query import _wrap
from faunadb.request_result import RequestResult
from faunadb.streams import Subscription


class HTTPBearerAuth(AuthBase):
    """Creates a bearer base auth object"""

    def auth_header(self):
        return "Bearer {}".format(self.secret)

    def __init__(self, secret):
        self.secret = secret

    def __eq__(self, other):
        return self.secret == getattr(other, 'secret', None)

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers['Authorization'] = self.auth_header()
        return r


class RuntimeEnvHeader:
    def __init__(self):
        self.pythonVersion = "{0}.{1}.{2}-{3}".format(*sys.version_info)
        self.driverVersion = pkg_version
        self.env = self.getRuntimeEnv()
        self.os = "{0}-{1}".format(platform.system(), platform.release())

    def getRuntimeEnv(self):
        env = [
            {
                "name": "Netlify",
                "check": lambda: "NETLIFY_IMAGES_CDN_DOMAIN" in os.environ
            },
            {
                "name": "Vercel",
                "check": lambda: "VERCEL" in os.environ
            },
            {
                "name": "Heroku",
                "check": lambda: "PATH" in os.environ and ".heroku" in os.environ["PATH"]
            },
            {
                "name": "AWS Lambda",
                "check": lambda: "AWS_LAMBDA_FUNCTION_VERSION" in os.environ
            },
            {
                "name": "GCP Cloud Functions",
                "check": lambda: "_" in os.environ and "google" in os.environ["_"]
            },
            {
                "name": "GCP Compute Instances",
                "check": lambda: "GOOGLE_CLOUD_PROJECT" in os.environ
            },
            {
                "name": "Azure Cloud Functions",
                "check": lambda: "WEBSITE_FUNCTIONS_AZUREMONITOR_CATEGORIES" in os.environ
            },
            {
                "name": "Azure Compute",
                "check": lambda: "ORYX_ENV_TYPE" in os.environ and "WEBSITE_INSTANCE_ID" in os.environ and os.environ["ORYX_ENV_TYPE"] == "AppService"
            }
        ]

        try:
            recognized = next(e for e in env if e.get("check")())
            if recognized is not None:
                return recognized.get("name")
        except:
            return "Unknown"

    def __str__(self):
        return "driver=python-{0}; runtime=python-{1} env={2}; os={3}".format(
            self.driverVersion, self.pythonVersion,
            self.env, self.os
        ).lower()


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
        """Produces a dictionary with a non-zero `X-Last-Seen-Txn` header; or,
        if one has not yet been set, the empty header dictionary."""
        t = self.time
        if t is None:
            return {}
        return {"X-Last-Seen-Txn": str(t)}

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
            endpoint=None,
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
        :param endpoint:
          Full URL for the FaunaDB server.
        """

        self.check_new_version()

        self.domain = domain
        self.scheme = scheme
        self.port = (443 if scheme ==
                     "https" else 80) if port is None else port

        self.auth = HTTPBearerAuth(secret)
        constructed_url = "%s://%s:%s" % (self.scheme, self.domain, self.port)
        self.base_url = self._normalize_endpoint(endpoint) if endpoint else constructed_url
        self.observer = observer

        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize

        self._last_txn_time = kwargs.get('last_txn_time') or _LastTxnTime()
        self._query_timeout_ms = kwargs.get('query_timeout_ms')
        if self._query_timeout_ms is not None:
            self._query_timeout_ms = int(self._query_timeout_ms)

        if ('session' not in kwargs) or ('counter' not in kwargs):
            self.session = Session()
            self.session.mount('https://', HTTPAdapter(pool_connections=pool_connections,
                                                       pool_maxsize=pool_maxsize))
            self.session.mount('http://', HTTPAdapter(pool_connections=pool_connections,
                                                      pool_maxsize=pool_maxsize))
            self.counter = _Counter(1)

            self.session.headers.update({
                "Keep-Alive": "timeout=5",
                "Accept-Encoding": "gzip",
                "Content-Type": "application/json;charset=utf-8",
                "X-Fauna-Driver": "python",
                "X-FaunaDB-API-Version": api_version,
                "X-Driver-Env": str(RuntimeEnvHeader())
            })
            if self._query_timeout_ms is not None:
                self.session.headers["X-Query-Timeout"] = str(
                    self._query_timeout_ms)
            self.session.timeout = timeout
        else:
            self.session = kwargs['session']
            self.counter = kwargs['counter']

    def check_new_version(self):
        response = get('https://pypi.org/pypi/faunadb/json')
        latest_version = response.json().get('info').get('version')

        if latest_version > pkg_version:
            msg1 = "New fauna version available {} => {}".format(
                pkg_version, latest_version)
            msg2 = "Changelog: https://github.com/fauna/faunadb-python/blob/v4/CHANGELOG.md"
            width = 80
            print('+' + '-' * width + '+')
            print('| ' + msg1 + ' ' * (width - len(msg1) - 1) + '|')
            print('| ' + msg2 + ' ' * (width - len(msg2) - 1) + '|')
            print('+' + '-' * width + '+')

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

    def get_query_timeout(self):
        """
        Get the query timeout for all queries.
        """
        return self._query_timeout_ms

    def _normalize_endpoint(self, endpoint):
      return endpoint.rstrip("/\\")

    def __del__(self):
        if self.counter.decrement() == 0:
            self.session.close()

    def query(self, expression, timeout_millis=None, tags=None, traceparent=None):
        """
        Use the FaunaDB query API.

        :param expression: A query. See :doc:`query` for information on queries.
        :param timeout_millis: Query timeout in milliseconds.
        :param tags: A dict of key-value pairs to send as the 'x-fauna-tags' header with the query
        :param traceparent: A W3C-compliant traceparent header to be sent with the query
        :return: Converted JSON response.
        """
        return self._execute("POST", "", _wrap(expression), with_txn_time=True, query_timeout_ms=timeout_millis, tags=tags, traceparent=traceparent)

    def stream(self, expression, options=None, on_start=None, on_error=None, on_version=None, on_history=None, on_set=None):
        """
        Creates a stream Subscription to the result of the given read-only expression. When
        executed.

        The subscription returned by this method does not issue any requests until
        the subscription's start method is called. Make sure to
        subscribe to the events of interest, otherwise the received events are simply
        ignored.

        :param expression:   A read-only expression.
        :param    options:   Object that configures the stream subscription. E.g set fields to return
        :param   on_start:   Callback for the stream's start event.
        :param   on_error:   Callback for the stream's error event.
        :param   on_version: Callback for the stream's version events.
        :param   on_history: Callback for the stream's history_rewrite events.
        :param   on_set:     Callback for the stream's set events.
        """
        subscription = Subscription(self, expression, options)
        subscription.on('start', on_start)
        subscription.on('error', on_error)
        subscription.on('version', on_version)
        subscription.on('history_rewrite', on_history)
        subscription.on('set', on_set)
        return subscription

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
                               last_txn_time=self._last_txn_time,
                               query_timeout_ms=self._query_timeout_ms)
        else:
            raise UnexpectedError(
                "Cannnot create a session client from a closed session", None)

    def _execute(self, action, path, data=None, query=None, with_txn_time=False, query_timeout_ms=None, tags=None, traceparent=None):
        """Performs an HTTP action, logs it, and looks for errors."""
        if query is not None:
            query = {k: v for k, v in query.items() if v is not None}

        headers = {}

        if query_timeout_ms is not None:
            headers["X-Query-Timeout"] = str(query_timeout_ms)

        if with_txn_time:
            headers.update(self._last_txn_time.request_header)

        if tags is not None:
            headers["x-fauna-tags"] = self._get_tags_string(tags)

        if traceparent is not None and self._is_valid_traceparent(traceparent):
            headers["traceparent"] = traceparent

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
        req = Request(action, url, params=query, data=to_json(
            data), auth=self.auth, headers=headers)
        return self.session.send(self.session.prepare_request(req))

    def _get_tags_string(self, tags_dict):
        if not isinstance(tags_dict, dict):
            raise Exception("Tags must be a dictionary")
        
        return ",".join(["=".join([k, tags_dict[k]]) for k in tags_dict])

    def _is_valid_traceparent(self, traceparent):
        return bool(re.match("^[\da-f]{2}-[\da-f]{32}-[\da-f]{16}-[\da-f]{2}$", traceparent))
