from faunadb.errors import FaunaError

class StreamError(FaunaError):
    """Stream Error"""
    def __init__(self, error, request_result = None):
        super(StreamError, self).__init__(error, request_result)
