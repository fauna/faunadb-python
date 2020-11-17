from .client import Connection
from .dispatcher import EventDispatcher


class Subscription(object):
    """
    A stream subscription which dispatches events received to the registered
    listener functions. This class must be constructed via the FaunaClient stream
    method.
    """
    def __init__(self, client, expression, options=None):
        self._client = Connection(client, expression, options)
        self._dispatcher = EventDispatcher()

    def start(self):
        """
        Initiates the underlying subscription network calls.
        """
        self._client.subscribe(self._dispatcher.dispatch)

    def on(self, event_type, callback):
        """
        Registers a callback for a specific event type.
        """
        self._dispatcher.on(event_type, callback)

    def close(self):
        """
        Stops the current subscription and closes the underlying network connection.
        """
        self._client.close()

    def __repr__(self):
        return "stream:Subscription(state=%s, expression=%s, options=%s)"%(self._client._state,
            self._client._query,self._client._options)
