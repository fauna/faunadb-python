"""Error types that methods in the FaunaDB client throw."""

from requests import codes


class InvalidResponse(Exception):
  """Thrown when the response from the server is unusable."""
  def __init__(self, description, response_data):
    self.description = description
    """Description of the kind of response expected."""
    self.response_data = response_data
    """Actual response data. (Type varies.)"""
    super(InvalidResponse, self).__init__(description)


#region FaunaHttpError

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
      raise HttpBadRequest(request_result)
    elif code == codes.unauthorized:
      raise HttpUnauthorized(request_result)
    elif code == codes.forbidden:
      raise HttpPermissionDenied(request_result)
    elif code == codes.not_found:
      raise HttpNotFound(request_result)
    elif code == codes.method_not_allowed:
      raise HttpMethodNotAllowed(request_result)
    elif code == codes.internal_server_error:
      raise HttpInternalError(request_result)
    elif code == codes.unavailable:
      raise HttpUnavailableError(request_result)
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

  def __repr__(self):
    return "%s(%s)" % (self.__class__.__name__, self.errors)


class HttpBadRequest(FaunaError):
  """HTTP 400 error."""
  pass


class HttpUnauthorized(FaunaError):
  """HTTP 401 error."""
  pass


class HttpPermissionDenied(FaunaError):
  """HTTP 403 error."""
  pass


class HttpNotFound(FaunaError):
  """HTTP 404 error."""
  pass


class HttpMethodNotAllowed(FaunaError):
  """HTTP 405 error."""
  pass


class HttpInternalError(FaunaError):
  """HTTP 500 error."""
  pass


class HttpUnavailableError(FaunaError):
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
    return "%s(%s, %s)" % (self.__class__.__name__, self.field, repr(self.description))


def get_or_invalid(dct, key):
  """Get a value from a dict or throw InvalidResponse."""
  try:
    return dct[key]
  except KeyError:
    raise InvalidResponse("Response should have '%s' key." % key, dct)
  except TypeError:
    raise InvalidResponse("Response should be a dict.", dct)
