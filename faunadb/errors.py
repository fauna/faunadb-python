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


class InvalidResponse(FaunaError):
  """Thrown when the response from the server is unusable."""


#region FaunaHttpError
class FaunaHttpError(FaunaError):
  """
  Error returned by the FaunaDB server.
  For documentation of error types, see the `docs <https://faunadb.com/documentation#errors>`__.
  """

  def __init__(self, response_dict):
    self.errors = [ErrorData.from_dict(error) for error in get_or_invalid(response_dict, "errors")]
    """List of all :py:class:`ErrorData` objects sent by the server."""
    super(FaunaHttpError, self).__init__(
      self.errors[0].description if self.errors else "(empty `errors`)")

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

class ErrorData(object):
  """
  Data for one error returned by the server.
  """

  @staticmethod
  def from_dict(dct):
    code = get_or_invalid(dct, "code")
    return ValidationFailed(dct) if code == "validation failed" else ErrorData(dct, code)

  def __init__(self, dct, code):
    self.code = code
    """Error code. See the many error codes `here <https://faunadb.com/documentation#errors>`__."""
    self.description = get_or_invalid(dct, "description")
    """Error description."""
    self.position = dct.get("position")
    """Position of the error in a query. May be None."""

  def __repr__(self):
    return "%s(%s)" % (self.__class__.__name__, self.position)

  def __eq__(self, other):
    return self.__class__ == other.__class__ and \
      self.description == other.description and \
      self.position == other.position


class ValidationFailed(ErrorData):
  """An ErrorData that also stores Failure information."""

  def __init__(self, dct):
    super(ValidationFailed, self).__init__(dct, "validation failed")
    self.failures = [Failure(failure) for failure in dct["failures"]]
    """List of all :py:class:`Failure` objects returned by the server."""

  def __repr__(self):
    return "%s(%s, %s)" % (self.__class__.__name__, self.position, self.failures)


class Failure(object):
  """
  Part of a :py:class:`ValidationFailed`.
  See the ``Invalid Data`` section of the `docs <https://faunadb.com/documentation#errors>`__.
  """

  def __init__(self, dct):
    self.code = get_or_invalid(dct, "code")
    """Failure code."""
    self.description = get_or_invalid(dct, "description")
    """Failure description."""
    self.field = get_or_invalid(dct, "field")
    """Field of the failure in the instance."""

  def __repr__(self):
    return "%s(%s, %s)" % (self.__class__.__name__, self.field, self.description)


def get_or_invalid(dct, key):
  """Get a value from a dict or throw InvalidResponse."""
  try:
    return dct[key]
  except KeyError:
    raise InvalidResponse("Response should have '%s' key, but got: %s" % (key, dct))
  except TypeError:
    raise InvalidResponse("Response should be a dict, but got: %s" % dct)
