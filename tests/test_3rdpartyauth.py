from __future__ import division
from datetime import date, datetime
from time import sleep, time
import string
import random


from faunadb.errors import BadRequest, NotFound, FaunaError, PermissionDenied
from faunadb.objects import FaunaTime,  Ref, SetRef, _Expr, Native, Query
from faunadb import query
from tests.helpers import FaunaTestCase


class ThirdPartyAuthTest(FaunaTestCase):
    @classmethod
    def setUpClass(cls):
        super(ThirdPartyAuthTest, cls).setUpClass()
        cls.collection_ref = cls._q(query.create_collection(
            {"name": "3rdpartyauth_test_coll"}))["ref"]

    #region Helpers

    @classmethod
    def _create(cls, n=0, **data):
        data["n"] = n
        return cls._q(query.create(cls.collection_ref, {"data": data}))

    @classmethod
    def _q(cls, query_json):
        return cls.client.query(query_json)

    @classmethod
    def _randStr(cls, n=10):
        letters = string.ascii_letters
        return ''.join(random.choice(letters) for i in range(n))

    def _assert_insufficient_permissions(self, q):
        self.assertRaises(PermissionDenied, lambda: self._q(q))

    def test_create_access_providers(self):
        providerName = 'provider_'
        issuerName = 'issuer_'
        jwksUri = 'https://xxx.auth0.com/somewhere'
        provider = self.admin_client.query(query.create_access_provider(
            {"name": providerName, "issuer": issuerName, "jwks_uri": jwksUri}))
        self.assertTrue(self.admin_client.query(
            query.exists(query.access_provider(providerName))))
        self.assertEqual(provider["name"], providerName)
        self.assertEqual(provider["issuer"], issuerName)
        self.assertEqual(provider["jwks_uri"], jwksUri)

        #fails if already exists
        self.assertRaises(BadRequest, lambda: self.admin_client.query(query.create_access_provider(
            {"name": providerName, "issuer": issuerName, "jwks_uri": jwksUri})))

        #fails without issuer
        self.assertRaises(BadRequest, lambda: self.admin_client.query(query.create_access_provider(
            {"name": providerName, "jwks_uri": jwksUri})))

        #fails with invalid uri
        jwksUri = 'https:/invalid-uri'
        self.assertRaises(BadRequest, lambda: self.admin_client.query(query.create_access_provider(
            {"name": providerName, "issuer": issuerName, "jwks_uri": jwksUri})))


    def test_access_provider(self):
        self.assertEqual(self._q(query.access_provider("pvd-name")),
                         Ref("pvd-name", Native.ACCESS_PROVIDERS))

    def test_access_providers(self):
        for i in range(10):
            providerName = 'provider_%d'%(i)
            issuerName = 'issuer_%d'%(i)
            jwksUri = 'https://xxx.auth0.com/uri%d'%(i)
            obj = {"name": providerName,
                   "issuer": issuerName, "jwks_uri": jwksUri}
            self.admin_client.query(query.create_access_provider(obj))
        self.assertEqual(self.admin_client.query(query.count(query.access_providers())), 10)
        self._assert_insufficient_permissions(query.paginate(query.access_providers()))

    def test_identity_has_identity(self):
        instance_ref = self.client.query(
        query.create(self.collection_ref, {"credentials": {"password": "sekrit"}}))["ref"]
        secret = self.client.query(
        query.login(instance_ref, {"password": "sekrit"}))["secret"]
        instance_client = self.client.new_session_client(secret=secret)

        self.assertTrue(instance_client.query(query.has_current_identity()))
        self.assertEqual(instance_client.query(query.current_identity()), instance_ref)

    def test_has_current_token(self):
        instance_ref = self._q(
            query.create(self.collection_ref, {"credentials": {"password": "sekrit"}}))["ref"]
        secret = self._q(
            query.login(instance_ref, {"password": "sekrit"}))["secret"]
        instance_client = self.client.new_session_client(secret=secret)

        self.assertTrue(instance_client.query(query.has_current_token()))
        self.assertFalse(self._q(query.has_current_token()))

    def test_has_current_identity(self):
        instance_ref = self._q(
            query.create(self.collection_ref, {"credentials": {"password": "sekrit"}}))["ref"]
        secret = self._q(
            query.login(instance_ref, {"password": "sekrit"}))["secret"]
        instance_client = self.client.new_session_client(secret=secret)

        self.assertTrue(instance_client.query(query.has_current_identity()))
        self.assertFalse(self._q(query.has_current_identity()))

    def test_create_accprov_with_roles(self):
        providerName = "provider_with_roles"
        issuerName = "issuer_%s"%(self._randStr())
        fullUri = "https: //$%s.auth0.com"%(self._randStr(4))
        roleOneName = "role_one_%s"%(self._randStr(4))
        roleTwoName = "role_two_%s"%(self._randStr(4))

        self.admin_client.query(query.create_role({
            "name": roleOneName,
            "privileges": [
                {
                    "resource": query.databases(),
                    "actions": {"read": True},
                },
            ],
        }))

        self.admin_client.query(query.create_role({
            "name": roleTwoName,
            "privileges": [
                {
                    "resource": query.databases(),
                    "actions": {"read": True},
                },
            ],
        }))

        provider = self.admin_client.query(query.create_access_provider({
            "name": providerName,
            "issuer": issuerName,
            "jwks_uri": fullUri,
            "roles": [
                query.role(roleOneName),
                {
                    "role": query.role(roleTwoName),
                    "predicate": query.query(query.lambda_("x", True)),
                },
            ],
        }))

        self.assertEqual(provider["name"], providerName)
        self.assertEqual(provider["issuer"], issuerName)
        self.assertEqual(provider["jwks_uri"], fullUri)
        self.assertTrue(isinstance(provider["roles"], list))

