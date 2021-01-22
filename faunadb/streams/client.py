from time import time

try:
    #python2
    from urllib import urlencode
except ImportError:
    #python3
    from urllib.parse import urlencode

from faunadb._json import parse_json_or_none, to_json
from faunadb.request_result import RequestResult
from hyper import HTTP20Connection

from .errors import StreamError
from .events import Error, parse_stream_request_result_or_none

VALID_FIELDS = {"diff", "prev", "document", "action"}


class Connection(object):
    """
    The internal stream client connection interface.
    This class handles the network side of a stream
    subscription.

    Current limitations:
    Python requests module uses HTTP1; hyper is used for HTTP/2
    """
    def __init__(self, client, expression, options):
        self._client = client
        self.options = options
        self.conn = None
        self._fields = None
        if isinstance(self.options, dict):
            self._fields = self.options.get("fields", None)
        elif hasattr(self.options, "fields"):
            self._fields = self.options.field
        if isinstance(self._fields, list):
            union = set(self._fields).union(VALID_FIELDS)
            if union != VALID_FIELDS:
                raise Exception("Valid fields options are %s, provided %s."%(VALID_FIELDS, self._fields))
        self._state = "idle"
        self._query = expression
        self._data = to_json(expression).encode()
        try:
            self.conn = HTTP20Connection(
                    self._client.domain, port=self._client.port, enable_push=True)
        except Exception as e:
            raise StreamError(e)

    def close(self):
        """
        Closes the stream subscription by aborting its underlying http request.
        """
        if self.conn is None:
            raise StreamError('Cannot close inactive stream subscription.')
        self.conn.close()
        self._state = 'closed'

    def subscribe(self, on_event):
        """Initiates the stream subscription."""
        if self._state != "idle":
            raise StreamError('Stream subscription already started.')
        try:
            self._state = 'connecting'
            headers = self._client.session.headers
            headers["Authorization"] = self._client.auth.auth_header()
            if self._client._query_timeout_ms is not None:
                    headers["X-Query-Timeout"] = str(self._client._query_timeout_ms)
            headers["X-Last-Seen-Txn"] = str(self._client.get_last_txn_time())
            start_time = time()
            url_params = ''
            if isinstance(self._fields, list):
                url_params= "?%s"%(urlencode({'fields': ",".join(self._fields)}))
            id = self.conn.request("POST", "/stream%s"%(url_params), body=self._data, headers=headers)
            self._state = 'open'
            self._event_loop(id, on_event, start_time)
        except Exception as e:
            if callable(on_event):
                on_event(Error(e), None)

    def _event_loop(self, stream_id, on_event, start_time):
        """ Event loop for the stream. """
        response = self.conn.get_response(stream_id)
        if 'x-txn-time' in response.headers:
            self._client.sync_last_txn_time(int(response.headers['x-txn-time'][0].decode()))
        try:
            for push in response.read_chunked():  # all pushes promised before response headers
                    raw = push.decode()
                    request_result = self._stream_chunk_to_request_result(response, raw, start_time, time())
                    event = parse_stream_request_result_or_none(request_result)
                    if event is not None and hasattr(event, 'txn'):
                        self._client.sync_last_txn_time(int(event.txn))
                    on_event(event, request_result)
                    if self._client.observer is not None:
                        self._client.observer(request_result)
        except Exception as e:
            self.error = e
            self.close()
            on_event(Error(e), None)

    def _stream_chunk_to_request_result(self, response, raw_chunk, start_time, end_time):
        """ Converts a stream chunk to a RequestResult. """
        response_content = parse_json_or_none(raw_chunk)
        return RequestResult(
            "POST", "/stream", self._query, self._data,
            raw_chunk, response_content, None, response.headers,
            start_time, end_time)

