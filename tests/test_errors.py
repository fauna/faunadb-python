from requests import codes

from faunadb import query
from faunadb.errors import ErrorData, Failure, ValidationFailed, FaunaError, BadRequest, \
  InternalError, MethodNotAllowed, NotFound, PermissionDenied, Unauthorized, UnavailableError, \
  InvalidResponse
from faunadb.objects import Ref

from tests.helpers import FaunaTestCase, mock_client

class ErrorsTest(FaunaTestCase):
  def test_request_result(self):
    err = capture_exception(lambda: self.client.query({"foo": "bar"}))
    assert err.request_result.request_content == {"foo": "bar"}

  def test_invalid_response(self):
    # Response must be valid JSON
    self.assertRaises(InvalidResponse, lambda: mock_client('I like fine wine').get(''))
    # Response must have "resource"
    self.assertRaises(InvalidResponse, lambda: mock_client('{"resoars": 1}').get(''))
    # Error response must have valid "code"
    code_client = mock_client('{"errors": [{"code": "foo"}]}', codes.bad_request)
    self.assertRaises(InvalidResponse, lambda: code_client.get(''))

  #region FaunaError
  def test_bad_request(self):
    self.assertRaises(BadRequest, lambda: self.client.query({"foo": "bar"}))
    # Tests of HttpBadRequest.errors go in ErrorData section.

  def test_unauthorized(self):
    client = self.get_client(secret="bad_key")
    assert_http_error(
      lambda: client.query(query.get(self.db_ref)), Unauthorized, "unauthorized")

  def test_permission_denied(self):
    # Create client with client key
    client = self.get_client(
      secret=self.root_client.query(
        query.create(Ref("keys"), query.object(database=self.db_ref, role="client")))["secret"]
    )

    exception = capture_exception(lambda: client.query(query.paginate(Ref("databases"))))
    assert isinstance(exception, PermissionDenied)
    assert_error(exception, "permission denied", ["paginate"])

  def test_not_found(self):
    assert_http_error(lambda: self.client.get("classes/not_found"), NotFound, "not found")

  def test_method_not_allowed(self):
    assert_http_error(
      lambda: self.client.delete("classes"), MethodNotAllowed, "method not allowed")

  def test_internal_error(self):
    # pylint: disable=line-too-long
    code_client = mock_client(
      '{"errors": [{"code": "internal server error", "description": "sample text", "stacktrace": []}]}',
      codes.internal_server_error)
    assert_http_error(lambda: code_client.get("error"), InternalError, "internal server error")

  def test_unavailable_error(self):
    client = mock_client(
      '{"errors": [{"code": "unavailable", "description": "on vacation"}]}',
      codes.unavailable)
    assert_http_error(lambda: client.get(''), UnavailableError, "unavailable")
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
      "unique": True,
      "active": True
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

  def test_repr(self):
    err = ErrorData("code", "desc", None)
    assert repr(err) == "ErrorData('code', 'desc', None)"

    failure = Failure("code", "desc", ["a", "b"])
    vf = ValidationFailed("vf_desc", ["vf"], [failure])
    assert repr(vf) == "ValidationFailed('vf_desc', ['vf'], [Failure('code', 'desc', ['a', 'b'])])"

  def _assert_query_error(self, q, code, position=None):
    position = position or []
    assert_error(capture_exception(lambda: self.client.query(q)), code, position)


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
