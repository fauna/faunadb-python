from requests import codes

from faunadb.errors import FaunaError, HttpBadRequest, HttpInternalError, \
  HttpMethodNotAllowed, HttpNotFound, HttpPermissionDenied, HttpUnauthorized, \
  HttpUnavailableError, InvalidResponse

from helpers import get_client, FaunaTestCase, mock_client

class ErrorsTest(FaunaTestCase):
  def test_invalid_response(self):
    # Response must be valid json
    self.assertRaises(InvalidResponse, lambda: mock_client('I like fine wine').get(''))
    # Response must have "resource"
    self.assertRaises(InvalidResponse, lambda: mock_client('{"resoars": 1}').get(''))
    # Error response must have valid "code"
    code_client = mock_client('{"errors": [{"code": "foo"}]}', codes.bad_request)
    self.assertRaises(InvalidResponse, lambda: code_client.get(''))

  #region HTTP errors
  def test_http_bad_request(self):
    self.assertRaises(HttpBadRequest, lambda: self.client.query({"foo": "bar"}))
    # Tests of HttpBadRequest.errors go in ErrorData section.

  def test_http_unauthorized(self):
    client = get_client("bad_key")
    assert_http_error(lambda: client.get(self.db_ref), HttpUnauthorized, "unauthorized")

  def test_http_permission_denied(self):
    assert_http_error(
      lambda: self.client.get("databases"), HttpPermissionDenied, "permission denied")

  def test_http_not_found(self):
    assert_http_error(lambda: self.client.get("classes/not_found"), HttpNotFound, "not found")

  def test_http_method_not_allowed(self):
    assert_http_error(
      lambda: self.client.delete("classes"), HttpMethodNotAllowed, "method not allowed")

  def test_internal_error(self):
    assert_http_error(lambda: self.client.get("error"), HttpInternalError, "internal server error")

  def test_unavailable_error(self):
    client = mock_client(
      '{"errors": [{"code": "unavailable", "description": "on vacation"}]}',
      codes.unavailable)
    assert_http_error(lambda: client.get(''), HttpUnavailableError, "unavailable")
  #endregion

  #region ErrorData
  def test_invalid_expression(self):
    self._assert_query_error({"foo": "bar"}, "invalid expression")

  def test_unbound_variable(self):
    self._assert_query_error({"var": "x"}, "unbound variable")

  def test_invalid_argument(self):
    self._assert_query_error({"add": [1, "two"]}, "invalid argument", ["add", 1])

  def test_instance_not_found(self):
    # Must be a reference to a real class or else we get InvalidExpression
    self.client.post("classes", {"name": "foofaws"})
    self._assert_query_error({"get": {"@ref": "classes/foofaws/123"}}, "instance not found")

  def test_value_not_found(self):
    self._assert_query_error({"select": ["a"], "from": {"object": {}}}, "value not found")

  def test_instance_already_exists(self):
    self.client.post("classes", {"name": "duplicates"})
    ref = self.client.post("classes/duplicates", {})["ref"]
    self._assert_query_error({"create": ref}, "instance already exists", ["create"])
  #endregion

  #region InvalidData
  def test_invalid_type(self):
    self._assert_invalid_data("classes", {"name": 123}, "invalid type", ["name"])

  def test_value_required(self):
    self._assert_invalid_data("classes", {}, "value required", ["name"])

  def test_duplicate_value(self):
    self.client.post("classes", {"name": "gerbils"})
    self.client.post("indexes", {
      "name": "gerbils_by_x",
      "source": {"@ref": "classes/gerbils"},
      "terms": [{"path": "data.x"}],
      "unique": True
    })
    self.client.post("classes/gerbils", {"data": {"x": 1}})
    self._assert_invalid_data(
      "classes/gerbils", {"data": {"x": 1}}, "duplicate value", ["data", "x"])

  def _assert_invalid_data(self, class_name, data, code, field):
    exception = capture_exception(lambda: self.client.post(class_name, data))
    assert_error(exception, "validation failed", [])
    failures = exception.errors[0].failures
    assert len(failures) == 1
    failure = failures[0]
    assert failure.code == code
    assert failure.field == field

  #endregion

  def _assert_query_error(self, query, code, position=None):
    position = position or []
    assert_error(capture_exception(lambda: self.client.query(query)), code, position)


def capture_exception(func):
  try:
    func()
  except FaunaError as exception:
    return exception


def assert_http_error(func, exception_cls, code):
  exception = capture_exception(func)
  assert isinstance(exception, exception_cls)
  assert_error(exception, code)


def assert_error(exception, code, position=None):
  assert len(exception.errors) == 1
  error = exception.errors[0]
  assert error.code == code
  assert error.position == position
