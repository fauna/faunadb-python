"""Error types that methods in the FaunaDB client throw."""
# pylint: disable=redefined-builtin
from builtins import object

from requests import codes


class InvalidResponse(Exception):
  """Thrown when the response from the server is unusable."""
  def __init__(self, description, response_data):
    self.description = description
    """Description of the kind of response expected."""
    self.response_data = response_data
    """Actual response data. (Type varies.)"""
    super(InvalidResponse, self).__init__(description)


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
      raise FaunaError(request_result)

  def __init__(self, request_result):
    response = request_result.response_content
    self.errors = [ErrorData.from_dict(error) for error in get_or_invalid(response, "errors")]
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
  def from_dict(dct):
    code = get_or_invalid(dct, "code")
    description = get_or_invalid(dct, "description")
    position = dct.get("position")
    if code == "validation failed":
      failures = [Failure.from_dict(failure) for failure in get_or_invalid(dct, "failures")]
      return ValidationFailed(description, position, failures)
    else:
      return ErrorData(code, description, position)

  def __init__(self, code, description, position):
    self.code = code
    """Error code. See all error codes `here <https://faunadb.com/documentation#errors>`__."""
    self.description = description
    """Error description."""
    self.position = position
    """Position of the error in a query. May be None."""

  def __repr__(self):
    return "ErrorData(%s, %s, %s)" % (repr(self.code), repr(self.description), repr(self.position))

  def __eq__(self, other):
    return self.__class__ == other.__class__ and \
      self.description == other.description and \
      self.position == other.position


class ValidationFailed(ErrorData):
  """An ErrorData that also stores Failure information."""

  def __init__(self, description, position, failures):
    super(ValidationFailed, self).__init__("validation failed", description, position)
    self.failures = failures
    """List of all :py:class:`Failure` objects returned by the server."""

  def __repr__(self):
    return "ValidationFailed(%s, %s, %s)" % \
      (repr(self.description), repr(self.position), repr(self.failures))


class Failure(object):
  """
  Part of a :py:class:`ValidationFailed`.
  See the ``Invalid Data`` section of the `docs <https://faunadb.com/documentation#errors>`__.
  """

  @staticmethod
  def from_dict(dct):
    return Failure(
      get_or_invalid(dct, "code"),
      get_or_invalid(dct, "description"),
      get_or_invalid(dct, "field"))

  def __init__(self, code, description, field):
    self.code = code
    """Failure code."""
    self.description = description
    """Failure description."""
    self.field = field
    """Field of the failure in the instance."""

  def __repr__(self):
    return "Failure(%s, %s, %s)" % (repr(self.code), repr(self.description), repr(self.field))


def get_or_invalid(dct, key):
  """Get a value from a dict or throw InvalidResponse."""
  try:
    return dct[key]
  except KeyError:
    raise InvalidResponse("Response should have '%s' key." % key, dct)
  except TypeError:
    raise InvalidResponse("Response should be a dict.", dct)
