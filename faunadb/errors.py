"""Error types that methods in the FaunaDB client throw."""

class FaunaError(Exception):
  """Base class for all FaunaDB errors."""
  pass

class InvalidQuery(FaunaError):
  """Thrown when a query is malformed."""
  pass

class InvalidValue(FaunaError):
  """Thrown when bad data is put into a Field of a Model."""
  def __init__(self, message="The field value is not valid."):
    super(InvalidValue, self).__init__(message)

class InvalidValue(FaunaError):
  """Thrown when a value cannot be accepted."""
  def __init__(self, message="The field value is not valid."):
    super(InvalidValue, self).__init__(message)


#region HTTPError
class FaunaHTTPError(FaunaError):
  """Error in FaunaDB server connection."""
  def __init__(self, response_dict):
    if "error" in response_dict:
      self.errors = [response_dict["error"]]
    else:
      self.errors = response_dict["errors"]
    self.reason = response_dict.get("reason", "")
    self.parameters = response_dict.get("parameters", {})
    super(FaunaHTTPError, self).__init__(self.reason or self.errors[0])

class BadRequest(FaunaHTTPError):
  """HTTP 400 error."""
  pass


class Unauthorized(FaunaHTTPError):
  """HTTP 401 error."""
  pass


class PermissionDenied(FaunaHTTPError):
  """HTTP 403 error."""
  pass


class NotFound(FaunaHTTPError):
  """HTTP 404 error."""
  pass


class MethodNotAllowed(FaunaHTTPError):
  """HTTP 405 error."""
  pass


class InternalError(FaunaHTTPError):
  """HTTP 500 error."""
  pass


class UnavailableError(FaunaHTTPError):
  """HTTP 503 error."""
  pass
#endregion
