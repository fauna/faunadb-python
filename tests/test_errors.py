from faunadb import query
from faunadb.errors import (AuthenticationFailedError, BadRequest, ErrorData,
                            Failure, FunctionCallError,
                            InstanceAlreadyExistsError, InternalError,
                            InvalidArgumentError, InvalidExpressionError,
                            InvalidTokenError, InvalidWriteTimeError,
                            MissingIdentityError, NotFound, PermissionDenied,
                            Unauthorized, UnavailableError, UnexpectedError,
                            ValidationError)
from faunadb.objects import Native
from faunadb.query import (_Expr, add, collection, create, create_collection,
                           create_function, create_key, get, ref, var)
from requests import codes

from tests.helpers import FaunaTestCase, mock_client


class TestObj(object):
    def __str__(self):
        return "TestObj"


class ErrorsTest(FaunaTestCase):

    # region UnexpectedError
    def test_json_error(self):
        # Response must be valid JSON
        err = self.assert_raises(
            UnexpectedError, lambda: mock_client("I like fine wine").query(''))
        rr = err.request_result
        self.assertIsNone(rr.response_content)
        self.assertEqual(rr.response_raw, "I like fine wine")

    def test_json_serialization(self):
        msg = r"Unserializable object TestObj of type <class '(tests\.)?test_errors\.TestObj'>"
        self.assertRaisesRegexCompat(
            UnexpectedError, msg, lambda: self.client.query(TestObj()))

    def test_resource_error(self):
        # Response must have "resource"
        self.assertRaises(UnexpectedError, lambda: mock_client(
            '{"resoars": 1}').query(''))

    def test_unexpected_error_code(self):
        self.assertRaises(UnexpectedError, lambda: mock_client(
            '{"errors": []}', 1337).query(''))
    # endregion

    # region FaunaError
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
        self._assert_http_error(lambda: code_client.query(
            "error"), InternalError, "internal server error")

    def test_unavailable_error(self):
        client = mock_client(
            '{"errors": [{"code": "unavailable", "description": "on vacation"}]}',
            codes.unavailable)
        self._assert_http_error(lambda: client.query(
            ''), UnavailableError, "unavailable")
    # endregion

    def test_query_error(self):
        self._assert_query_error(
            add(1, "two"), InvalidArgumentError, "invalid argument", ["add", 1])

    def test_error_data_equality(self):
        e1 = ErrorData("code", "desc", ["pos"], [Failure("fc", "fd", ["ff"])])
        e2 = ErrorData("code", "desc", ["pos"], [Failure("fc", "fd", ["ff"])])
        self.assertEqual(e1, e2)
        self.assertNotEqual(e1, ErrorData(
            "code", "desc", ["pos"], [Failure("fc", "fd", [])]))

    def test_failure_equality(self):
        f1 = Failure("code", "desc", ["pos"])
        f2 = Failure("code", "desc", ["pos"])
        self.assertEqual(f1, f2)
        self.assertNotEqual(f1, Failure("code", "desc", ["pos", "more"]))

    # region ErrorData
    def test_invalid_expression(self):
        self._assert_query_error(
            _Expr({"foo": "bar"}), InvalidExpressionError, "invalid expression")

    def test_unbound_variable(self):
        self._assert_query_error(
            var("x"), InvalidExpressionError, "invalid expression")

    def test_invalid_argument(self):
        self._assert_query_error(
            add([1, "two"]), InvalidArgumentError, "invalid argument", ["add", 1])

    def test_instance_not_found(self):
        # Must be a reference to a real collection or else we get InvalidExpression
        self.client.query(create_collection({"name": "foofaws"}))
        self._assert_query_error(
            get(ref(collection("foofaws"), "123")),
            NotFound,
            "instance not found")

    def test_call_error(self):
        self.client.query(query.create_function({"name": "failed", "body": query.query(
            query.lambda_("x", query.divide(query.var("x"), 0))
        )}))
        self._assert_query_error(
            query.call(query.function("failed"), "x"),
            FunctionCallError,
            "call error")

    def test_invalid_currenct_identity(self):
        self._assert_query_error(
            query.current_identity(),
            MissingIdentityError,
            "missing identity")

    def test_invalid_token(self):
        self._assert_query_error(
            query.current_token(),
            InvalidTokenError,
            "invalid token")

    def test_invalid_write_time(self):
        self.client.query(create_collection({"name": "invalid_time"}))
        r = self.client.query(create(collection("invalid_time"), {}))["ref"]
        self._assert_query_error(
            query.insert(
                r,
                query.time_add(query.now(), 5, "days"),
                "create",
                {"data": {"color": "yellow"}}
            ),
            InvalidWriteTimeError,
            "invalid write time")

    def test_call_error(self):
        self.client.query(query.create_function({"name": "stack_overflow", "body": query.query(
            query.lambda_("x", query.call(
                query.function("stack_overflow"), query.var("x")))
        )}))
        self._assert_query_error(
            query.call(query.function("failed")),
            FunctionCallError,
            "stack overflow")

    def test_authentication_failed(self):
        self.client.query(query.create_collection({"name": "users"}))
        self.client.query(query.create_index({
            "name": "user_by_email",
            "source": query.collection("users"),
            "terms": [{"field": ["data", "email"]}]
        }))
        self._assert_query_error(
            query.login(query.match(query.index("user_by_email"),
                        "some@email.com"), {"password": "password"}),
            AuthenticationFailedError,
            "authenticationfailed")

    def test_value_not_found(self):
        self._assert_query_error(query.select(
            "a", {}), NotFound, "value not found", ["from"])

    def test_instance_already_exists(self):
        self.client.query(create_collection({"name": "duplicates"}))
        r = self.client.query(create(collection("duplicates"), {}))["ref"]
        self._assert_query_error(
            create(r, {}), InstanceAlreadyExistsError, "instance already exists", ["create"])
    # endregion

    # region InvalidData
    def test_invalid_type(self):
        exception = self.assert_raises(ValidationError,
                                       lambda: self.client.query(create_collection({"name": 123})))
        self._assert_error(exception, "validation failed",
                           ['create_collection'])
        failures = exception.errors[0].failures
        self.assertEqual(len(failures), 1)
        failure = failures[0]
        self.assertEqual(failure.code, "invalid type")
        self.assertEqual(failure.field, ["name"])

    def test_repr(self):
        err = ErrorData("code", "desc", None, None)
        self.assertEqual(repr(
            err), "ErrorData(code='code', description='desc', position=None, failures=None, cause=None)")

        failure = Failure("code", "desc", ["a", "b"])
        err = ErrorData("code", "desc", ["pos"], [failure])
        self.assertEqual(
            repr(err),
            "ErrorData(code='code', description='desc', position=['pos'], failures=[Failure(code='code', description='desc', field=['a', 'b'])], cause=None)")

    # region private

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

    # endregion
