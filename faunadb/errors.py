"""Error types that methods in the FaunaDB client throw."""

class FaunaError(Exception):
  """Base class for all FaunaDB errors."""
  pass


class InvalidQuery(FaunaError):
  """Thrown when a query is malformed."""
  pass


class InvalidValue(FaunaError):
  """Thrown when a value cannot be accepted."""
  def __init__(self, message="The field value is not valid."):
    super(InvalidValue, self).__init__(message)

#region HTTPError
class FaunaHttpError(FaunaError):
  """
  Error returned by the FaunaDB server.
  For documentation of error types, see the `docs <https://faunadb.com/documentation#errors>`__.
  """

  def __init__(self, response_dict):
    self.errors = [ErrorData.from_dict(error) for error in response_dict["errors"]]
    """List of all :py:class:`ErrorData` objects sent by the server."""
    super(FaunaHttpError, self).__init__(self.errors[0].description)

  def __repr__(self):
    return "%s(%s)" % (self.__class__.__name__, [repr(error) for error in self.errors])


class HttpBadRequest(FaunaHttpError):
  """HTTP 400 error."""
  pass


class HttpUnauthorized(FaunaHttpError):
  """HTTP 401 error."""
  pass


class HttpPermissionDenied(FaunaHttpError):
  """HTTP 403 error."""
  pass


class HttpNotFound(FaunaHttpError):
  """HTTP 404 error."""
  pass


class HttpMethodNotAllowed(FaunaHttpError):
  """HTTP 405 error."""
  pass


class HttpInternalError(FaunaHttpError):
  """HTTP 500 error."""
  pass


class HttpUnavailableError(FaunaHttpError):
  """HTTP 503 error."""
  pass

#endregion

#region ErrorData

class ErrorData(object):
  @staticmethod
  def from_dict(dct):
    return _ERROR_CODE_TO_CLASS[dct["code"]](dct)

  def __init__(self, dct):
    self.description = dct["description"]
    self.position = dct.get("position")

  def __repr__(self):
    return "%s(%s)" % (self.__class__.__name__, self.position)

  def __eq__(self, other):
    return self.__class__ == other.__class__ and \
      self.description == other.description and \
      self.position == other.position

#region Analogues of HTTP errors

class BadRequest(ErrorData):
  code = "bad request"

class Unauthorized(ErrorData):
  code = "unauthorized"


class PermissionDenied(ErrorData):
  code = "permission denied"


class NotFound(ErrorData):
  code = "not found"


class MethodNotAllowed(ErrorData):
  code = "method not allowed"


class InternalError(ErrorData):
  code = "internal server error"


class UnavailableError(ErrorData):
  code = "unavailable"

#endregion


class InvalidExpression(ErrorData):
  code = "invalid expression"


class UnboundVariable(ErrorData):
  code = "unbound variable"


class InvalidArgument(ErrorData):
  code = "invalid argument"


class DivideByZero(ErrorData):
  code = "divide by zero"


class InstanceNotFound(ErrorData):
  code = "instance not found"


class ValueNotFound(ErrorData):
  code = "value not found"


class InstanceAlreadyExists(ErrorData):
  code = "instance already exists"


class ValidationFailed(ErrorData):
  code = "validation failed"

  def __init__(self, dct):
    super(ValidationFailed, self).__init__(dct)
    self.failures = [Failure.from_dict(failure) for failure in dct["failures"]]

  def __repr__(self):
    return "%s(%s, %s)" % (self.__class__.__name__, self.position, self.failures)

# pylint thinks __subclasses__ doesn't exist
# pylint:disable=no-member
_ERROR_CODE_TO_CLASS = {cls.code: cls for cls in ErrorData.__subclasses__()}

#endregion

#region Failure

class Failure(object):
  """
  Part of a :py:class:`ValidationFailed`.
  See the ``Invalid Data`` section of the `docs <https://faunadb.com/documentation#errors>`__.
  """

  @staticmethod
  def from_dict(dct):
    return _FAILURE_CODE_TO_CLASS[dct["code"]](dct)

  def __init__(self, dct):
    self.description = dct["description"]
    self.field = dct["field"]

  def __repr__(self):
    return "%s(%s, %s)" % (self.__class__.__name__, self.field, self.description)


class InvalidType(Failure):
  code = "invalid type"


class ValueRequired(Failure):
  code = "value required"


class DuplicateValue(Failure):
  code = "duplicate value"


_FAILURE_CODE_TO_CLASS = {cls.code: cls for cls in Failure.__subclasses__()}

#endregion

