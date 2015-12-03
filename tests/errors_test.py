from requests import codes

from faunadb.errors import FaunaHttpError, HttpBadRequest, HttpInternalError, \
  HttpMethodNotAllowed, HttpNotFound, HttpPermissionDenied, HttpUnauthorized, \
  HttpUnavailableError, InvalidResponse
from faunadb.errors import DivideByZero, InstanceAlreadyExists, InternalError, InvalidArgument,\
  InvalidExpression, InstanceNotFound, MethodNotAllowed, NotFound, PermissionDenied, Unauthorized, \
  UnavailableError, UnboundVariable, ValidationFailed, ValueNotFound
from faunadb.errors import DuplicateValue, InvalidType, ValueRequired

from test_case import get_client, FaunaTestCase, mock_client

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
    assert_http_error(lambda: client.get(self.db_ref), HttpUnauthorized, Unauthorized)

  def test_http_permission_denied(self):
    assert_http_error(lambda: self.client.get("databases"), HttpPermissionDenied, PermissionDenied)

  def test_http_not_found(self):
    assert_http_error(lambda: self.client.get("classes/not_found"), HttpNotFound, NotFound)

  def test_http_method_not_allowed(self):
    assert_http_error(lambda: self.client.delete("classes"), HttpMethodNotAllowed, MethodNotAllowed)

  def test_internal_error(self):
    assert_http_error(lambda: self.client.get("error"), HttpInternalError, InternalError)

  def test_unavailable_error(self):
    client = mock_client(
      '{"errors": [{"code": "unavailable", "description": "on vacation"}]}',
      codes.unavailable)
    assert_http_error(lambda: client.get(''), HttpUnavailableError, UnavailableError)
  #endregion

  #region ErrorData
  def test_invalid_expression(self):
    self._assert_query_error({"foo": "bar"}, InvalidExpression, [])

  def test_unbound_variable(self):
    self._assert_query_error({"var": "x"}, UnboundVariable, [])

  def test_invalid_argument(self):
    self._assert_query_error({"add": [1, "two"]}, InvalidArgument, ["add", 1])

  def test_divide_by_zero(self):
    self._assert_query_error({"divide": [1, 0]}, DivideByZero, [])

  def test_instance_not_found(self):
    # Must be a reference to a real class or else we get InvalidExpression
    self.client.post("classes", {"name": "foofaws"})
    self._assert_query_error({"get": {"@ref": "classes/foofaws/123"}}, InstanceNotFound, [])

  def test_value_not_found(self):
    self._assert_query_error({"select": ["a"], "from": {"object": {}}}, ValueNotFound, [])

  def test_instance_already_exists(self):
    self.client.post("classes", {"name": "duplicates"})
    ref = self.client.post("classes/duplicates", {})["ref"]
    self._assert_query_error({"create": ref}, InstanceAlreadyExists, ["create"])
  #endregion

  #region InvalidData
  def test_invalid_type(self):
    ex = capture_exception(lambda: self.client.post("classes", {"name": 123}))
    assert_validation(ex, InvalidType, ["name"])

  def test_value_required(self):
    ex = capture_exception(lambda: self.client.post("classes", {}))
    assert_validation(ex, ValueRequired, ["name"])

  def test_duplicate_value(self):
    self.client.post("classes", {"name": "gerbils"})
    self.client.post("indexes", {
      "name": "gerbils_by_x",
      "source": {"@ref": "classes/gerbils"},
      "terms": [{"path": "data.x"}],
      "unique": True
    })
    self.client.post("classes/gerbils", {"data": {"x": 1}})
    ex = capture_exception(lambda: self.client.post("classes/gerbils", {"data": {"x": 1}}))
    assert_validation(ex, DuplicateValue, ['data', 'x'])
  #endregion

  def _assert_query_error(self, query, cls, position=None):
    assert_error(self._capture_query_exception(query), cls, position)

  def _capture_query_exception(self, query):
    return capture_exception(lambda: self.client.query(query))


def capture_exception(func):
  try:
    func()
  except FaunaHttpError as exception:
    return exception


def assert_http_error(func, exception_cls, error_cls):
  exception = capture_exception(func)
  assert isinstance(exception, exception_cls)
  assert_error(exception, error_cls)


def assert_error(exception, cls, position=None):
  assert len(exception.errors) == 1
  error = exception.errors[0]
  assert isinstance(error, cls)
  assert error.position == position


def assert_validation(exception, cls, field):
  assert_error(exception, ValidationFailed, [])
  failures = exception.errors[0].failures
  assert len(failures) == 1
  failure = failures[0]
  assert isinstance(failure, cls)
  assert failure.field == field

