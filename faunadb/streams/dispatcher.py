import logging

class EventDispatcher(object):
    """
    Event dispatch interface for stream subscription.
    """
    def __init__(self):
        self.callbacks = {}

    def on(self, event_type, callback):
        """
        Subscribe to an event.
        """
        if callable(callback):
            self.callbacks[event_type] = callback
        elif callback is not None:
            raise Exception("Callback for event `%s` is not callable."%(event_type))

    def _noop(self, event, request_result):
        """
        Default callback for unregistered event types.
        """
        logging.debug("Unhandled stream event %s; %s"%(event, request_result))
        pass

    def dispatch(self, event, request_result):
        """
        Dispatch the given event to the appropriate listeners.
        """
        fn = self.callbacks.get(event.type, None)
        if fn is None:
            return self._noop(event, request_result)
        return fn(event)


