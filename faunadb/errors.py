"""Error types that methods in the FaunaDB client throw."""
# pylint: disable=redefined-builtin
from builtins import object

from requests import codes


def _get_or_raise(request_result, dct, key):
    if isinstance(dct, dict) and key in dct:
        return dct[key]
    else:
        raise UnexpectedError(
            "Response JSON does not contain expected key %s" % key, request_result)

# region FaunaError


class FaunaError(Exception):
    """
    Error returned by the FaunaDB server.
    For documentation of error types, see the `docs <https://fauna.com/documentation#errors>`__.
    """

    @staticmethod
    def raise_for_status_code(request_result):
        code = request_result.status_code
        # pylint: disable=no-member, too-many-return-statements
        if 200 <= code <= 299:
            pass
        elif code == codes.bad_request:
            raise BadRequest(request_result)
        elif code == codes.unauthorized:
            raise Unauthorized(request_result)
        elif code == codes.forbidden:
            raise PermissionDenied(request_result)
        elif code == codes.not_found:
            raise NotFound(request_result)
        elif code == codes.conflict:
            raise ContendedTransaction(request_result)
        elif code == codes.internal_server_error:
            raise InternalError(request_result)
        elif code == codes.unavailable:
            raise UnavailableError(request_result)
        else:
            raise UnexpectedError("Unexpected status code.", request_result)

    def __init__(self, description, request_result):
        super(FaunaError, self).__init__(description)
        self.request_result = request_result
        """:any:`RequestResult` for the request that caused this error."""


class UnexpectedError(FaunaError):
    """Error for when the server returns an unexpected kind of response."""
    pass


class HttpError(FaunaError):
    def __init__(self, request_result):
        self.errors = HttpError._get_errors(request_result)
        """List of all :py:class:`ErrorData` objects sent by the server."""
        super(HttpError, self).__init__(
            self._get_description(), request_result)

    @staticmethod
    def _get_errors(request_result):
        response = request_result.response_content
        errors = _get_or_raise(request_result, response, "errors")
        return [ErrorData.from_dict(error, request_result) for error in errors]

    def __str__(self):
        return repr(self.errors[0])

    def _get_description(self):
        return self.errors[0].description if self.errors else "(empty `errors`)"


class BadRequest(HttpError):
    """HTTP 400 error."""
    pass


class Unauthorized(HttpError):
    def __init__(self, request_result):
        super(Unauthorized, self).__init__(request_result)
        self.errors[0].description = "Unauthorized. Check that endpoint, schema, port and secret are correct during client’s instantiation"


class PermissionDenied(HttpError):
    """HTTP 403 error."""
    pass


class NotFound(HttpError):
    """HTTP 404 error."""
    pass


class ContendedTransaction(HttpError):
    """HTTP 409 error."""
    pass


class InternalError(HttpError):
    """HTTP 500 error."""
    pass


class UnavailableError(HttpError):
    """HTTP 503 error."""
    pass


# endregion

class ErrorData(object):
    """
    Data for one error returned by the server.
    """

    @staticmethod
    def from_dict(dct, request_result):
        return ErrorData(
            _get_or_raise(request_result, dct, "code"),
            _get_or_raise(request_result, dct, "description"),
            dct.get("position"),
            ErrorData.get_failures(dct, request_result),
            ErrorData.get_cause(dct, request_result))

    @staticmethod
    def get_failures(dct, request_result):
        if "failures" in dct:
            return [Failure.from_dict(failure, request_result) for failure in dct["failures"]]
        return None

    @staticmethod
    def get_cause(dct, request_result):
        if "cause" in dct:
            return [ErrorData.from_dict(cause, request_result) for cause in dct["cause"]]
        return None

    def __init__(self, code, description, position, failures, cause=None):
        self.code = code
        """Error code. See all error codes `here <https://fauna.com/documentation#errors>`__."""
        self.description = description
        """Error description."""
        self.position = position
        """Position of the error in a query. May be None."""
        self.failures = failures
        """Cause of the error. May be None."""
        self.cause = cause
        """
    List of all :py:class:`Failure` objects returned by the server.
    None unless code == "validation failed".
    """

    def __repr__(self):
        return "ErrorData(code=%s, description=%s, position=%s, failures=%s, cause=%s)" % \
               (repr(self.code), repr(self.description),
                repr(self.position), repr(self.failures),
                repr(self.cause))

    def __eq__(self, other):
        return self.__class__ == other.__class__ and \
            self.description == other.description and \
            self.position == other.position and \
            self.failures == other.failures and \
            self.cause == other.cause

    def __ne__(self, other):
        # pylint: disable=unneeded-not
        return not self == other


class Failure(object):
    """
    Part of the ``failures`` of an :py:class:`ErrorData`.
    See the ``Invalid Data`` section of the `docs <https://fauna.com/documentation#errors>`__.
    """

    @staticmethod
    def from_dict(dct, request_result):
        return Failure(
            _get_or_raise(request_result, dct, "code"),
            _get_or_raise(request_result, dct, "description"),
            _get_or_raise(request_result, dct, "field"))

    def __init__(self, code, description, field):
        self.code = code
        """Failure code."""
        self.description = description
        """Failure description."""
        self.field = field
        """Field of the failure in the instance."""

    def __repr__(self):
        return "Failure(code=%s, description=%s, field=%s)" % (repr(self.code), repr(self.description), repr(self.field))

    def __eq__(self, other):
        return self.code == other.code and \
            self.description == other.description and \
            self.field == other.field

    def __ne__(self, other):
        # pylint: disable=unneeded-not
        return not self == other
