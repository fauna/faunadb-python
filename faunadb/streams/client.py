from time import time

try:
    # python2
    from urllib import urlencode
except ImportError:
    # python3
    from urllib.parse import urlencode

from faunadb._json import parse_json_or_none, stream_content_to_json, to_json
from faunadb.request_result import RequestResult
import httpx

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
                raise Exception("Valid fields options are %s, provided %s." % (
                    VALID_FIELDS, self._fields))
        self._state = "idle"
        self._query = expression
        self._data = to_json(expression).encode()
        try:
            base_url = "https://%s:%s" % (self._client.domain, self._client.port)
            self.conn=httpx.Client(http2=True,http1=False, base_url=base_url, timeout=None)
        except Exception as error_msg:
            raise StreamError(error_msg)

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
                headers["X-Query-Timeout"] = str(
                    self._client._query_timeout_ms)
            headers["X-Last-Seen-Txn"] = str(self._client.get_last_txn_time())
            start_time = time()
            url_params = ''
            if isinstance(self._fields, list):
                url_params = "?%s" % (
                    urlencode({'fields': ",".join(self._fields)}))
            id = self.conn.stream("POST", "/stream%s" %
                                  (url_params), data=self._data, headers=dict(headers))
            
            self._state = 'open'
            self._event_loop(id, on_event, start_time)
        except Exception as error_msg:
            if callable(on_event):
                on_event(Error(error_msg), None)

    def _event_loop(self, stream_id, on_event, start_time):
        """ Event loop for the stream. """
        with stream_id as response:
            if 'x-txn-time' in response.headers:
                self._client.sync_last_txn_time(int(response.headers['x-txn-time']))
            try:
                buffer = ''
                for push in response.iter_bytes():

                    try:
                        chunk = push.decode()
                        buffer += chunk
                    except:
                        continue

                    result = stream_content_to_json(buffer)
                    buffer = result["buffer"]

                    for value in result["values"]:
                        request_result = self._stream_chunk_to_request_result(
                            response, value["raw"], value["content"], start_time, time())
                        event = parse_stream_request_result_or_none(request_result)

                        if event is not None and hasattr(event, 'txn'):
                            self._client.sync_last_txn_time(int(event.txn))
                        on_event(event, request_result)
                        if self._client.observer is not None:
                            self._client.observer(request_result)
            except Exception as error_msg:
                self.error = error_msg
                self.close()
                on_event(Error(error_msg), None)

    def _stream_chunk_to_request_result(self, response, raw, content, start_time, end_time):
        """ Converts a stream chunk to a RequestResult. """
        return RequestResult(
            "POST", "/stream", self._query, self._data,
            raw, content, None, response.headers,
            start_time, end_time)
