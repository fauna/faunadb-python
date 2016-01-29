"""Error types that methods in the FaunaDB client throw."""
# pylint: disable=redefined-builtin
from builtins import object

from requests import codes

class UnexpectedError(Exception):
  """Error for when the server returns an unexpected kind of response."""
  def __init__(self, description, request_result):
    super(UnexpectedError, self).__init__(description)
    self.request_result = request_result
    # :any:`RequestResult` for the request that caused this error.

  @staticmethod
  def get_or_raise(request_result, dct, key):
    if isinstance(dct, dict) and key in dct:
      return dct[key]
    else:
      raise UnexpectedError("Response JSON does not contain expected key %s" % key, request_result)

#region FaunaError

class FaunaError(Exception):
  """
  Error returned by the FaunaDB server.
  For documentation of error types, see the `docs <https://faunadb.com/documentation#errors>`__.
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
    elif code == codes.method_not_allowed:
      raise MethodNotAllowed(request_result)
    elif code == codes.internal_server_error:
      raise InternalError(request_result)
    elif code == codes.unavailable:
      raise UnavailableError(request_result)
    else:
      raise UnexpectedError("Unexpected status code.", request_result)

  def __init__(self, request_result):
    response = request_result.response_content
    errors_raw = UnexpectedError.get_or_raise(request_result, response, "errors")
    self.errors = [ErrorData.from_dict(error, request_result) for error in errors_raw]
    """List of all :py:class:`ErrorData` objects sent by the server."""
    super(FaunaError, self).__init__(
      self.errors[0].description if self.errors else "(empty `errors`)")
    self.request_result = request_result
    """:any:`RequestResult` for the request that caused this error."""


class BadRequest(FaunaError):
  """HTTP 400 error."""
  pass


class Unauthorized(FaunaError):
  """HTTP 401 error."""
  pass


class PermissionDenied(FaunaError):
  """HTTP 403 error."""
  pass


class NotFound(FaunaError):
  """HTTP 404 error."""
  pass


class MethodNotAllowed(FaunaError):
  """HTTP 405 error."""
  pass


class InternalError(FaunaError):
  """HTTP 500 error."""
  pass


class UnavailableError(FaunaError):
  """HTTP 503 error."""
  pass

#endregion

class ErrorData(object):
  """
  Data for one error returned by the server.
  """

  @staticmethod
  def from_dict(dct, request_result):
    code = UnexpectedError.get_or_raise(request_result, dct, "code")
    description = UnexpectedError.get_or_raise(request_result, dct, "description")
    position = dct.get("position")
    if "failures" in dct:
      failures = [Failure.from_dict(failure, request_result) for failure in dct["failures"]]
    else:
      failures = None
    return ErrorData(code, description, position, failures)

  def __init__(self, code, description, position, failures):
    self.code = code
    """Error code. See all error codes `here <https://faunadb.com/documentation#errors>`__."""
    self.description = description
    """Error description."""
    self.position = position
    """Position of the error in a query. May be None."""
    self.failures = failures
    """
    List of all :py:class:`Failure` objects returned by the server.
    None unless code == "validation failed".
    """

  def __repr__(self):
    return "ErrorData(%s, %s, %s, %s)" % \
           (repr(self.code), repr(self.description), repr(self.position), repr(self.failures))

  def __eq__(self, other):
    return self.__class__ == other.__class__ and \
      self.description == other.description and \
      self.position == other.position


class Failure(object):
  """
  Part of the ``failures`` of an :py:class:`ErrorData`.
  See the ``Invalid Data`` section of the `docs <https://faunadb.com/documentation#errors>`__.
  """

  @staticmethod
  def from_dict(dct, request_result):
    return Failure(
      UnexpectedError.get_or_raise(request_result, dct, "code"),
      UnexpectedError.get_or_raise(request_result, dct, "description"),
      UnexpectedError.get_or_raise(request_result, dct, "field"))

  def __init__(self, code, description, field):
    self.code = code
    """Failure code."""
    self.description = description
    """Failure description."""
    self.field = field
    """Field of the failure in the instance."""

  def __repr__(self):
    return "Failure(%s, %s, %s)" % (repr(self.code), repr(self.description), repr(self.field))
