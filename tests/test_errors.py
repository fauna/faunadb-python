from requests import codes

from faunadb.errors import ErrorData, Failure, ValidationFailed, BadRequest, InternalError, \
  MethodNotAllowed, NotFound, PermissionDenied, Unauthorized, UnavailableError, InvalidResponse
from faunadb.objects import Ref
from faunadb.query import add, create, get, _Expr, paginate, select, var

from tests.helpers import FaunaTestCase, mock_client

class ErrorsTest(FaunaTestCase):
  def test_request_result(self):
    err = self.assert_raises(BadRequest, lambda: self.client.query(_Expr({"foo": "bar"})))
    self.assertEqual(err.request_result.request_content, {"foo": "bar"})

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
    self.assertRaises(BadRequest, lambda: self.client.query(_Expr({"foo": "bar"})))
    # Tests of HttpBadRequest.errors go in ErrorData section.

  def test_unauthorized(self):
    client = self.get_client(secret="bad_key")
    self.assert_http_error(
      lambda: client.query(get(self.db_ref)), Unauthorized, "unauthorized")

  def test_permission_denied(self):
    # Create client with client key
    client = self.get_client(
      secret=self.root_client.query(
        create(Ref("keys"), {"database": self.db_ref, "role": "client"}))["secret"]
    )

    exception = self.assert_raises(
      PermissionDenied,
      lambda: client.query(paginate(Ref("databases"))))
    self.assert_error(exception, "permission denied", ["paginate"])

  def test_not_found(self):
    self.assert_http_error(lambda: self.client.get("classes/not_found"), NotFound, "not found")

  def test_method_not_allowed(self):
    self.assert_http_error(
      lambda: self.client.delete("classes"), MethodNotAllowed, "method not allowed")

  def test_internal_error(self):
    # pylint: disable=line-too-long
    code_client = mock_client(
      '{"errors": [{"code": "internal server error", "description": "sample text", "stacktrace": []}]}',
      codes.internal_server_error)
    self.assert_http_error(lambda: code_client.get("error"), InternalError, "internal server error")

  def test_unavailable_error(self):
    client = mock_client(
      '{"errors": [{"code": "unavailable", "description": "on vacation"}]}',
      codes.unavailable)
    self.assert_http_error(lambda: client.get(''), UnavailableError, "unavailable")
  #endregion

  #region ErrorData
  def test_invalid_expression(self):
    self._assert_query_error(_Expr({"foo": "bar"}), BadRequest, "invalid expression")

  def test_unbound_variable(self):
    self._assert_query_error(var("x"), BadRequest, "unbound variable")

  def test_invalid_argument(self):
    self._assert_query_error(add([1, "two"]), BadRequest, "invalid argument", ["add", 1])

  def test_instance_not_found(self):
    # Must be a reference to a real class or else we get InvalidExpression
    self.client.post("classes", {"name": "foofaws"})
    self._assert_query_error(
      get(Ref("classes/foofaws/123")),
      NotFound,
      "instance not found")

  def test_value_not_found(self):
    self._assert_query_error(select("a", {}), NotFound, "value not found")

  def test_instance_already_exists(self):
    self.client.post("classes", {"name": "duplicates"})
    ref = self.client.post("classes/duplicates", {})["ref"]
    self._assert_query_error(create(ref, {}), BadRequest, "instance already exists", ["create"])
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
    exception = self.assert_raises(BadRequest, lambda: self.client.post(class_name, data))
    self.assert_error(exception, "validation failed", [])
    failures = exception.errors[0].failures
    self.assertEqual(len(failures), 1)
    failure = failures[0]
    self.assertEqual(failure.code, code)
    self.assertEqual(failure.field, field)
  #endregion

  def test_repr(self):
    err = ErrorData("code", "desc", None)
    self.assertEqual(repr(err), "ErrorData('code', 'desc', None)")

    failure = Failure("code", "desc", ["a", "b"])
    vf = ValidationFailed("vf_desc", ["vf"], [failure])
    self.assertEqual(
      repr(vf),
      "ValidationFailed('vf_desc', ['vf'], [Failure('code', 'desc', ['a', 'b'])])")

  def _assert_query_error(self, q, exception_class, code, position=None):
    position = position or []
    self.assert_error(
      self.assert_raises(exception_class, lambda: self.client.query(q)),
      code, position)

  def assert_http_error(self, action, exception_cls, code):
    self.assert_error(self.assert_raises(exception_cls, action), code)

  def assert_error(self, exception, code, position=None):
    self.assertEqual(len(exception.errors), 1)
    error = exception.errors[0]
    self.assertEqual(error.code, code)
    self.assertEqual(error.position, position)
