# pylint: disable=redefined-builtin
from builtins import object


class RequestResult(object):
  """Stores information about a single request and response."""
  # pylint: disable=too-many-instance-attributes

  def __init__(
      self, client,
      method, path, query, request_content,
      response_content, status_code, response_headers,
      start_time, end_time):
    self.client = client
    """The :any:`Client`."""
    self.method = method
    """"GET", "POST", "PUT", "PATCH", or "DELETE"."""
    self.path = path
    """Path that was queried. Relative to client's domain."""
    self.query = query
    """URL query. ``None`` unless ``method == GET``. *Not* related to :any:`Client.query`."""
    self.request_content = request_content
    """Request data."""
    self.response_content = response_content
    """
    Value returned by the response.
    Includes "resource" wrapper dict, or may be an "errors" dict instead.
    """
    self.status_code = status_code
    """HTTP status code."""
    self.response_headers = response_headers
    """A dictionary of headers with case-insensitive keys."""
    self.start_time = start_time
    """Time the request started."""
    self.end_time = end_time
    """Time the response was received."""

  @property
  def time_taken(self):
    """``end_time - start_time``"""
    return self.end_time - self.start_time

  @property
  def auth(self):
    """``(user, pass)`` used by the client."""
    return self.client.session.auth
