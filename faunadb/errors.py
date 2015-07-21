"Error types that FaunaDB client throws."

class FaunaError(Exception):
  "Base class for all FaunaDB errors."
  def __init__(self, message):
    super(FaunaError, self).__init__(message)

class InvalidQuery(FaunaError):
  "Thrown when a query is malformed."
  pass

class DatabaseError(FaunaError):
  "Thrown when the database behaves in an unexpected way."
  pass

class InvalidValue(FaunaError):
  "Thrown when bad data is put into a Field of a Model."
  def __init__(self, message="The field value is not valid."):
    super(InvalidValue, self).__init__(message)

#region HTTPError
class FaunaHTTPError(FaunaError):
  "Error in FaunaDB server connection."

  def __init__(self, response):
    params = response.json()
    if "error" in params:
      self.errors = [params["error"]]
    else:
      self.errors = params["errors"]
    self.reason = params.get("reason", "")
    self.parameters = params.get("parameters", {})
    super(FaunaHTTPError, self).__init__(self.reason or self.errors[0])

class BadRequest(FaunaHTTPError):
  "HTTP 400 Error."
  pass

class Unauthorized(FaunaHTTPError):
  "HTTP 401 Error."
  pass

class PermissionDenied(FaunaHTTPError):
  "HTTP 403 Error."
  pass

class NotFound(FaunaHTTPError):
  "HTTP 404 Error."
  pass

class MethodNotAllowed(FaunaHTTPError):
  "HTTP 405 Error."
  pass

class InternalError(FaunaHTTPError):
  "HTTP 500 Error."
  pass

class UnavailableError(FaunaHTTPError):
  "HTTP 503 Error."
  pass
#endregion
