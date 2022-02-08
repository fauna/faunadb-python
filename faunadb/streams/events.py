
from faunadb._json import parse_json_or_none
from faunadb.errors import BadRequest, PermissionDenied


def parse_stream_request_result_or_none(request_result):
    """
    Parses a stream RequestResult into a stream Event type.
    """
    event = None
    parsed = request_result.response_content
    if parsed is None:
        return UnknownEvent(request_result)
    evt_type = parsed.get('type', None)
    if evt_type == "start":
        event = Start(parsed)
    elif evt_type is None and 'errors' in parsed:
        event = Error(BadRequest(request_result))
    elif evt_type == 'error':
        event = Error(parsed)
    elif evt_type == 'version':
        event = Version(parsed)
    elif evt_type == 'set':
        event = Set(parsed)
    elif evt_type == 'history_rewrite':
        event = HistoryRewrite(parsed)
    else:
        event = UnknownEvent(request_result)

    return event


class Event(object):
    """
    A stream event.
    """
    def __init__(self, event_type):
        self.type = event_type

class ProtocolEvent(Event):
    """
    Stream protocol event.
    """
    def __init__(self, event_type):
        super(ProtocolEvent, self).__init__(event_type)


class Start(ProtocolEvent):
    """
    Stream's start event. A stream subscription always begins with a start event.
    Upcoming events are guaranteed to have transaction timestamps equal to or greater than
    the stream's start timestamp.

    :param data: Data
    :param txn: Timestamp
    """
    def __init__(self, parsed):
        super(Start, self).__init__('start')
        self.event = parsed['event']
        self.txn = parsed['txn']

    def __repr__(self):
        return "stream:event:Start(event=%s, txn=%d)"%(self.event, self.txn)

class Error(ProtocolEvent):
    """
    An error event is fired both for client and server errors that may occur as
    a result of a subscription.
    """
    def __init__(self, parsed):
        super(Error, self).__init__('error')
        self.error = None
        self.code = None
        self.description = None
        if isinstance(parsed, dict):
            if 'event' in parsed:
                self.error = parsed['event']
                if isinstance(parsed['event'], dict):
                    self.code = parsed['event'].get('code', None)
                    self.description = parsed['event'].get('description', None)
            elif 'errors' in parsed:
                self.error = parsed['errors']
            else:
                self.error = parsed
        else:
            self.error = parsed

    def __repr__(self):
        return "stream:event:Error(%s)"%(self.error)

class HistoryRewrite(Event):
    """
    A history rewrite event occurs upon any modifications to the history of the
    subscribed document.

    :param data:  Data
    :param txn: Timestamp
    """
    def __init__(self, parsed):
        super(HistoryRewrite, self).__init__('history_rewrite')
        if isinstance(parsed, dict):
            self.event = parsed.get('event', None)
            self.txn = parsed.get('txn')

        def __repr__(self):
            return "stream:event:HistoryRewrite(event=%s, txn=%s)" % (self.event, self.txn)

class Version(Event):
    """
    A version event occurs upon any modifications to the current state of the
    subscribed document.

    :param data:  Data
    :param txn: Timestamp
    """
    def __init__(self, parsed):
        super(Version, self).__init__('version')
        if isinstance(parsed, dict):
            self.event = parsed.get('event', None)
            self.txn = parsed.get('txn')

    def __repr__(self):
        return "stream:event:Version(event=%s, txn=%s)" % (self.event, self.txn)

class Set(Event):
    """
    A set event occurs upon any modifications to the current state of the
    subscribed set.

    :param event: Data
    :param txn: Timestamp
    """
    def __init__(self, parsed):
        super(Set, self).__init__('set')
        if isinstance(parsed, dict):
            self.event = parsed.get('event', None)
            self.txn = parsed.get('txn')

    def __repr__(self):
        return "stream:event:Set(event=%s, txn=%s)" % (self.event, self.txn)

class UnknownEvent(Event):
    """
    Unknown stream event.
    """
    def __init__(self, parsed):
        super(UnknownEvent, self).__init__(None)
        self.event = 'unknown'
        self.event = parsed

