"Error types that FaunaDB client throws."

class FaunaError(Exception):
  "Base class for all FaunaDB errors."
  def __init__(self, message):
    super(FaunaError, self).__init__(message)

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

class UnavailableError(FaunaError):
  pass

class InvalidQuery(FaunaError):
  "Thrown when a query is malformed."
  pass
