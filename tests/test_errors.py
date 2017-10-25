from requests import codes

from faunadb import query
from faunadb.errors import ErrorData, Failure, BadRequest, InternalError, \
  NotFound, PermissionDenied, Unauthorized, UnavailableError, UnexpectedError
from faunadb.objects import Native
from faunadb.query import create, create_class, create_key, class_, add, get, var, ref, _Expr

from tests.helpers import FaunaTestCase, mock_client

class TestObj(object):
  def __str__(self):
    return "TestObj"

class ErrorsTest(FaunaTestCase):

  #region UnexpectedError
  def test_json_error(self):
    # Response must be valid JSON
    err = self.assert_raises(UnexpectedError, lambda: mock_client("I like fine wine").query(''))
    rr = err.request_result
    self.assertIsNone(rr.response_content)
    self.assertEqual(rr.response_raw, "I like fine wine")

  def test_json_serialization(self):
    msg = r"Unserializable object TestObj of type <class '(tests\.)?test_errors\.TestObj'>"
    self.assertRaisesRegexCompat(UnexpectedError, msg, lambda: self.client.query(TestObj()))

  def test_resource_error(self):
    # Response must have "resource"
    self.assertRaises(UnexpectedError, lambda: mock_client('{"resoars": 1}').query(''))

  def test_unexpected_error_code(self):
    self.assertRaises(UnexpectedError, lambda: mock_client('{"errors": []}', 1337).query(''))
  #endregion

  #region FaunaError
  def test_unauthorized(self):
    client = self.root_client.new_session_client(secret="bad_key")
    self._assert_http_error(
      lambda: client.query(get(self.db_ref)), Unauthorized, "unauthorized")

  def test_permission_denied(self):
    # Create client with client key
    client = self.root_client.new_session_client(
      secret=self.root_client.query(
        create_key({"database": self.db_ref, "role": "client"}))["secret"]
    )

    exception = self.assert_raises(
      PermissionDenied,
      lambda: client.query(query.paginate(Native.DATABASES)))
    self._assert_error(exception, "permission denied", ["paginate"])

  def test_internal_error(self):
    # pylint: disable=line-too-long
    code_client = mock_client(
      '{"errors": [{"code": "internal server error", "description": "sample text", "stacktrace": []}]}',
      codes.internal_server_error)
    self._assert_http_error(lambda: code_client.query("error"), InternalError, "internal server error")

  def test_unavailable_error(self):
    client = mock_client(
      '{"errors": [{"code": "unavailable", "description": "on vacation"}]}',
      codes.unavailable)
    self._assert_http_error(lambda: client.query(''), UnavailableError, "unavailable")
  #endregion

  def test_query_error(self):
    self._assert_query_error(add(1, "two"), BadRequest, "invalid argument", ["add", 1])

  def test_error_data_equality(self):
    e1 = ErrorData("code", "desc", ["pos"], [Failure("fc", "fd", ["ff"])])
    e2 = ErrorData("code", "desc", ["pos"], [Failure("fc", "fd", ["ff"])])
    self.assertEqual(e1, e2)
    self.assertNotEqual(e1, ErrorData("code", "desc", ["pos"], [Failure("fc", "fd", [])]))

  def test_failure_equality(self):
    f1 = Failure("code", "desc", ["pos"])
    f2 = Failure("code", "desc", ["pos"])
    self.assertEqual(f1, f2)
    self.assertNotEqual(f1, Failure("code", "desc", ["pos", "more"]))

  #region ErrorData
  def test_invalid_expression(self):
    self._assert_query_error(_Expr({"foo": "bar"}), BadRequest, "invalid expression")

  def test_unbound_variable(self):
    self._assert_query_error(var("x"), BadRequest, "unbound variable")

  def test_invalid_argument(self):
    self._assert_query_error(add([1, "two"]), BadRequest, "invalid argument", ["add", 1])

  def test_instance_not_found(self):
    # Must be a reference to a real class or else we get InvalidExpression
    self.client.query(create_class({"name": "foofaws"}))
    self._assert_query_error(
      get(ref(class_("foofaws"), "123")),
      NotFound,
      "instance not found")

  def test_value_not_found(self):
    self._assert_query_error(query.select("a", {}), NotFound, "value not found")

  def test_instance_already_exists(self):
    self.client.query(create_class({"name": "duplicates"}))
    r = self.client.query(create(class_("duplicates"), {}))["ref"]
    self._assert_query_error(create(r, {}), BadRequest, "instance already exists", ["create"])
  #endregion

  #region InvalidData
  def test_invalid_type(self):
    exception = self.assert_raises(BadRequest,
                                   lambda: self.client.query(create_class({"name": 123})))
    self._assert_error(exception, "validation failed", [])
    failures = exception.errors[0].failures
    self.assertEqual(len(failures), 1)
    failure = failures[0]
    self.assertEqual(failure.code, "invalid type")
    self.assertEqual(failure.field, ["name"])

  def test_repr(self):
    err = ErrorData("code", "desc", None, None)
    self.assertEqual(repr(err), "ErrorData('code', 'desc', None, None)")

    failure = Failure("code", "desc", ["a", "b"])
    err = ErrorData("code", "desc", ["pos"], [failure])
    self.assertEqual(
      repr(err),
      "ErrorData('code', 'desc', ['pos'], [Failure('code', 'desc', ['a', 'b'])])")

  #region private

  def _assert_query_error(self, q, exception_class, code, position=None):
    position = position or []
    self._assert_error(
      self.assert_raises(exception_class, lambda: self.client.query(q)),
      code, position)

  def _assert_http_error(self, action, exception_cls, code):
    self._assert_error(self.assert_raises(exception_cls, action), code)

  def _assert_error(self, exception, code, position=None):
    self.assertEqual(len(exception.errors), 1)
    error = exception.errors[0]
    self.assertEqual(error.code, code)
    self.assertEqual(error.position, position)

  #endregion
