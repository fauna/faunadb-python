from __future__ import division
from datetime import date, datetime
from time import sleep

from faunadb.errors import BadRequest, NotFound
from faunadb.objects import FaunaTime, Ref, SetRef, _Expr, Native
from faunadb import query
from tests.helpers import FaunaTestCase

class QueryTest(FaunaTestCase):
  @classmethod
  def setUpClass(cls):
    super(QueryTest, cls).setUpClass()

    cls.collection_ref = cls.client.query(query.create_collection({"name": "widgets"}))["ref"]
    cls.n_index_ref = cls.client.query(query.create_index({
      "name": "widgets_by_n",
      "active": True,
      "source": cls.collection_ref,
      "terms": [{"field": ["data", "n"]}]
    }))["ref"]

    cls.m_index_ref = cls.client.query(query.create_index({
      "name": "widgets_by_m",
      "active": True,
      "source": cls.collection_ref,
      "terms": [{"field": ["data", "m"]}]
    }))["ref"]

    cls.z_index_ref = cls._q(query.create_index({
      "name": "widgets_by_z",
      "active": True,
      "source": cls.collection_ref,
      "values": [{"field": ["data", "z"]}]
    }))["ref"]

  #region Helpers

  @classmethod
  def _create(cls, n=0, **data):
    data["n"] = n

    return cls._q(query.create(cls.collection_ref, {"data": data}))

  @classmethod
  def _q(cls, query_json):
    return cls.client.query(query_json)

  @classmethod
  def _set_to_list(cls, _set):
    return cls._q(query.paginate(_set, size=1000))["data"]

  def _assert_bad_query(self, q):
    self.assertRaises(BadRequest, lambda: self._q(q))

  #endregion

  #region Basic forms

  def test_abort(self):
    self._assert_bad_query(query.abort("aborting"))

  def test_at(self):
    document = self._create(n=1)
    ref = document["ref"]
    ts = document["ts"]
    prev_ts = ts - 1

    # Add previous event
    data = {"n": 0}
    self._q(query.insert(ref, prev_ts, "create", {"data": data}))

    # Get version from previous event
    old = self._q(query.at(prev_ts, query.get(ref)))
    self.assertEqual(old["data"], data)

  def test_let(self):
    self.assertEqual(self._q(query.let({"x": 1, "y": 2}, query.var("x"))), 1)
    self.assertEqual(self._q(query.let(x = 1, y = 2).in_(query.var("x"))), 1)

  def test_if(self):
    self.assertEqual(self._q(query.if_(True, "t", "f")), "t")
    self.assertEqual(self._q(query.if_(False, "t", "f")), "f")

  def test_do(self):
    ref = self._create()["ref"]
    self.assertEqual(self._q(query.do(query.delete(ref), 1)), 1)
    self.assertFalse(self._q(query.exists(ref)))

    self.assertEqual(self._q(query.do(1)), 1)
    self.assertEqual(self._q(query.do(1, 2)), 2)
    self.assertEqual(self._q(query.do([1, 2])), [1, 2])

  def test_lambda_query(self):
    invalid_lambda = lambda: query.add(1, 2)
    self.assertRaises(ValueError,
                      lambda: self._q(query.map_(query.lambda_query(invalid_lambda), [])))

    expr = query.map_(query.lambda_query(lambda a: query.add(a, 1)),
                      [1, 2, 3])
    self.assertEqual(self._q(expr), [2, 3, 4])

  def test_lambda_query_multiple_args(self):
    #pylint: disable=unnecessary-lambda
    expr = query.map_(query.lambda_query(lambda a, b: query.add(a, b)),
                      [[1, 1], [2, 2], [3, 3]])
    self.assertEqual(self._q(expr), [2, 4, 6])

  def test_call_function(self):
    self._q(query.create_function({
      "name": "concat_with_slash",
      "body": query.query(lambda a, b: query.concat([a, b], "/"))
    }))

    self.assertEqual(self._q(query.call(query.function("concat_with_slash"), "a", "b")), "a/b")

  def test_echo_query(self):
    body = self._q(query.query(lambda a, b: query.concat([a, b], "/")))
    bodyEchoed = self._q(body)

    self.assertEqual(body, bodyEchoed)

  #endregion

  #region Collection functions

  def test_map(self):
    # This is also test_lambda_expr (can't test that alone)
    self.assertEqual(
      self._q(query.map_(lambda a: query.multiply(2, a), [1, 2, 3])),
      [2, 4, 6])

    self._create(n=10)
    self._create(n=10)
    self._create(n=10)

    page = query.paginate(query.match(self.n_index_ref, 10))
    ns = query.map_(lambda a: query.select(["data", "n"], query.get(a)), page)
    self.assertEqual(self._q(ns), {"data": [10, 10, 10]})

  def test_foreach(self):
    refs = [self._create()["ref"], self._create()["ref"]]
    self._q(query.foreach(query.delete, refs))
    for ref in refs:
      self.assertFalse(self._q(query.exists(ref)))

  def test_filter(self):
    evens = query.filter_(lambda a: query.equals(query.modulo(a, 2), 0), [1, 2, 3, 4])
    self.assertEqual(self._q(evens), [2, 4])

    # Works on page too
    ref = self._create(n=11, m=12)["ref"]
    self._create(n=11)
    self._create(n=11)

    page = query.paginate(query.match(self.n_index_ref, 11))
    refs_with_m = query.filter_(lambda a: query.contains(["data", "m"], query.get(a)), page)
    self.assertEqual(self._q(refs_with_m), {"data": [ref]})

  def test_take(self):
    self.assertEqual(self._q(query.take(1, [1, 2])), [1])
    self.assertEqual(self._q(query.take(3, [1, 2])), [1, 2])
    self.assertEqual(self._q(query.take(-1, [1, 2])), [])

  def test_drop(self):
    self.assertEqual(self._q(query.drop(1, [1, 2])), [2])
    self.assertEqual(self._q(query.drop(3, [1, 2])), [])
    self.assertEqual(self._q(query.drop(-1, [1, 2])), [1, 2])

  def test_prepend(self):
    self.assertEqual(self._q(query.prepend([1, 2, 3], [4, 5, 6])), [1, 2, 3, 4, 5, 6])

  def test_append(self):
    self.assertEqual(self._q(query.append([4, 5, 6], [1, 2, 3])), [1, 2, 3, 4, 5, 6])

  def test_collection_predicates(self):
    self.assertTrue(self._q(query.is_empty([])))
    self.assertFalse(self._q(query.is_empty([1, 2, 3])))

    self.assertFalse(self._q(query.is_nonempty([])))
    self.assertTrue(self._q(query.is_nonempty([1, 2, 3])))

    self._create(n=111)
    self.assertFalse(self._q(query.is_empty(query.paginate(query.match(self.n_index_ref, 111)))))
    self.assertTrue(self._q(query.is_empty(query.paginate(query.match(self.n_index_ref, 112)))))

    self.assertTrue(self._q(query.is_nonempty(query.paginate(query.match(self.n_index_ref, 111)))))
    self.assertFalse(self._q(query.is_nonempty(query.paginate(query.match(self.n_index_ref, 112)))))

  #endregion

  #region Read functions

  def test_get(self):
    document = self._create()
    self.assertEqual(self._q(query.get(document["ref"])), document)

  def test_key_from_secret(self):
    db_ref = self.admin_client.query(
      query.create_database({"name": "database_for_key_from_secret_test"}))["ref"]
    key = self.admin_client.query(query.create_key({
      "database": db_ref,
      "role": "server"}))

    self.assertEqual(
      self.admin_client.query(query.key_from_secret(key["secret"]))["ref"],
      key["ref"]
    )

  def test_paginate(self):
    n_value = 200

    refs = [
      self._create(n=n_value)["ref"],
      self._create(n=n_value)["ref"],
      self._create(n=n_value)["ref"]
    ]

    test_set = query.match(self.n_index_ref, n_value)
    self.assertEqual(self._q(query.paginate(test_set)), {"data": refs})

    data = []
    page1 = self._q(query.paginate(test_set, size=1))
    data.extend(page1["data"])
    page2 = self._q(query.paginate(test_set, size=1, after=page1["after"]))
    data.extend(page2["data"])
    self.assertEqual(data, [refs[0], refs[1]])

    self.assertEqual(self._q(query.paginate(test_set, sources=True)), {
      "data": [
        {"sources": [SetRef(test_set)], "value": refs[0]},
        {"sources": [SetRef(test_set)], "value": refs[1]},
        {"sources": [SetRef(test_set)], "value": refs[2]}
      ]
    })

  def test_exists(self):
    ref = self._create()["ref"]
    self.assertTrue(self._q(query.exists(ref)))
    self._q(query.delete(ref))
    self.assertFalse(self._q(query.exists(ref)))

  #endregion

  #region Write functions

  def test_create(self):
    document = self._create()
    self.assertIn("ref", document)
    self.assertIn("ts", document)
    self.assertEqual(document["ref"].collection(), self.collection_ref)

  def test_update(self):
    ref = self._create()["ref"]
    got = self._q(query.update(ref, {"data": {"m": 1}}))
    self.assertEqual(got["data"], {"n": 0, "m": 1})

  def test_replace(self):
    ref = self._create()["ref"]
    got = self._q(query.replace(ref, {"data": {"m": 1}}))
    self.assertEqual(got["data"], {"m": 1})

  def test_delete(self):
    ref = self._create()["ref"]
    self._q(query.delete(ref))
    self.assertFalse(self._q(query.exists(ref)))

  def test_insert(self):
    document = self._create(n=1)
    ref = document["ref"]
    ts = document["ts"]
    prev_ts = ts - 1

    # Add previous event
    inserted = {"data": {"n": 0}}
    self._q(query.insert(ref, prev_ts, "create", inserted))

    # Get version from previous event
    old = self._q(query.get(ref, ts=prev_ts))
    self.assertEqual(old["data"], {"n": 0})

  def test_remove(self):
    document = self._create(n=0)
    ref = document["ref"]

    # Change it
    new_instance = self._q(query.replace(ref, {"data": {"n": 1}}))
    self.assertEqual(self._q(query.get(ref)), new_instance)

    # Delete that event
    self._q(query.remove(ref, new_instance["ts"], "create"))

    # Assert that it was undone
    self.assertEqual(self._q(query.get(ref)), document)

  def test_create_collection(self):
    self._q(query.create_collection({"name": "collection_for_test"}))

    self.assertTrue(self._q(query.exists(query.collection("collection_for_test"))))

  def test_create_database(self):
    self.admin_client.query(query.create_database({"name": "database_for_test"}))

    self.assertTrue(self.admin_client.query(query.exists(query.database("database_for_test"))))

  def test_create_index(self):
    self._q(query.create_index({
      "name": "index_for_test",
      "active": True,
      "source": query.collection("widgets")}))

    self.assertTrue(self._q(query.exists(query.index("index_for_test"))))

  def test_create_key(self):
    self.admin_client.query(query.create_database({"name": "database_for_key_test"}))

    resource = self.admin_client.query(query.create_key({
      "database": query.database("database_for_key_test"),
      "role": "server"}))

    new_client = self.admin_client.new_session_client(secret=resource["secret"])

    new_client.query(query.create_collection({"name": "collection_for_test"}))

    self.assertTrue(new_client.query(query.exists(query.collection("collection_for_test"))))

  def test_create_function(self):
    self._q(query.create_function({"name": "a_function", "body": query.query(lambda x: x)}))

    self.assertTrue(self._q(query.exists(query.function("a_function"))))

  def test_create_role(self):
    self.admin_client.query(query.create_role({
      "name": "a_role",
      "privileges": {
        "resource": query.collections(),
        "actions": {"read": True}
      }
    }))

    self.assertTrue(self.admin_client.query(query.exists(query.role("a_role"))))

  def test_move_database(self):
    self.admin_client.query(query.create_database({"name": "mvdb_src"}))
    self.admin_client.query(query.create_database({"name": "mvdb_dst"}))
    self.admin_client.query(query.move_database(query.database("mvdb_src"), query.database("mvdb_dst")))
    self.assertEqual(self.admin_client.query(
        query.exists(query.database("mvdb_src"))), False)
    self.assertEqual(self.admin_client.query(query.exists(query.database("mvdb_src", query.database("mvdb_dst")))), True)

  #endregion

  #region Sets

  def test_events(self):
    instance_ref = self._create(n=1000)["ref"]

    self._q(query.update(instance_ref, {"data": {"n": 1001}}))
    self._q(query.delete(instance_ref))

    events = self._q(query.paginate(query.events(instance_ref)))["data"]

    self.assertEqual(len(events), 3)

    self.assertEqual(events[0]["action"], "create")
    self.assertEqual(events[0]["document"], instance_ref)

    self.assertEqual(events[1]["action"], "update")
    self.assertEqual(events[1]["document"], instance_ref)

    self.assertEqual(events[2]["action"], "delete")
    self.assertEqual(events[2]["document"], instance_ref)

  def test_singleton_events(self):
    instance_ref = self._create(n=1000)["ref"]

    self._q(query.update(instance_ref, {"data": {"n": 1001}}))
    self._q(query.delete(instance_ref))

    events = self._q(query.paginate(query.events(query.singleton(instance_ref))))["data"]

    self.assertEqual(len(events), 2)

    self.assertEqual(events[0]["action"], "add")
    self.assertEqual(events[0]["document"], instance_ref)

    self.assertEqual(events[1]["action"], "remove")
    self.assertEqual(events[1]["document"], instance_ref)


  def test_match(self):
    n_value = 100
    m_value = 200
    ref_n = self._create(n=n_value)["ref"]
    ref_nm = self._create(n=n_value, m=m_value)["ref"]
    self._create(m=m_value)

    q = query.match(self.n_index_ref, n_value)
    self.assertEqual(self._set_to_list(q), [ref_n, ref_nm])

  def test_union(self):
    n_value = 101
    m_value = 201
    ref_n = self._create(n=n_value)["ref"]
    ref_m = self._create(m=m_value)["ref"]
    ref_nm = self._create(n=n_value, m=m_value)["ref"]

    q = query.union(query.match(self.n_index_ref, n_value),
                    query.match(self.m_index_ref, m_value))
    self.assertEqual(self._set_to_list(q), [ref_n, ref_m, ref_nm])

  def test_intersection(self):
    n_value = 102
    m_value = 202
    ref_nm = self._create(n=n_value, m=m_value)["ref"]
    self._create(n=n_value)
    self._create(m=m_value)

    q = query.intersection(query.match(self.n_index_ref, n_value),
                           query.match(self.m_index_ref, m_value))
    self.assertEqual(self._set_to_list(q), [ref_nm])

  def test_difference(self):
    n_value = 103
    m_value = 203
    ref_n = self._create(n=n_value)["ref"]
    self._create(m=m_value)
    self._create(n=n_value, m=m_value)

    q = query.difference(query.match(self.n_index_ref, n_value),
                         query.match(self.m_index_ref, m_value))
    self.assertEqual(self._set_to_list(q), [ref_n]) # but not ref_nm

  def test_distinct(self):
    self._create(z=0)
    self._create(z=0)
    self._create(z=1)
    self._create(z=1)
    self._create(z=1)

    distinct = query.distinct(query.match(self.z_index_ref))

    self.assertEqual(self._set_to_list(distinct), [0, 1])

  def test_join(self):
    join_refs = [self._create(n=12)["ref"], self._create(n=12)["ref"]]
    assoc_refs = [self._create(m=ref)["ref"] for ref in join_refs]

    source = query.match(self.n_index_ref, 12)
    self.assertEqual(self._set_to_list(source), join_refs)

    # For each obj with n=12, get the set of elements whose data.m refers to it.
    joined = query.join(source, lambda a: query.match(self.m_index_ref, a))
    self.assertEqual(self._set_to_list(joined), assoc_refs)

  def test_range(self):
    data = list(range(1, 20))

    self._q(query.create_collection({"name": "range_test"}))
    self._q(query.create_index({"name": "range_idx", "source": query.collection("range_test"), "active": True, "values": [{"field": ["data", "value"]}]}))
    self._q(query.foreach(query.lambda_query( lambda x:
    query.create(query.collection("range_test"), {"data": {"value": x}})), data)
    )
    m = query.match(query.index("range_idx"))

    q1 = query.select("data", query.paginate(query.range(m, 3, 8)))
    q2 = query.select("data", query.paginate(query.range(m, 17, 18)))
    q3 = query.select("data", query.paginate(query.range(m, 19, 0)))

    self.assertEqual(self._q(q1), [3, 4, 5, 6, 7, 8])
    self.assertEqual(self._q(q2), [17, 18])
    self.assertEqual(self._q(q3), [])

  #endregion

  #region Authentication

  def test_login_logout(self):
    instance_ref = self.client.query(
      query.create(self.collection_ref, {"credentials": {"password": "sekrit"}}))["ref"]
    secret = self.client.query(
      query.login(instance_ref, {"password": "sekrit"}))["secret"]
    instance_client = self.client.new_session_client(secret=secret)

    self.assertEqual(instance_client.query(
      query.select("ref", query.get(Ref("self", Ref("widgets", Native.COLLECTIONS))))), instance_ref)

    self.assertTrue(instance_client.query(query.logout(True)))

  def test_identify(self):
    instance_ref = self.client.query(
      query.create(self.collection_ref, {"credentials": {"password": "sekrit"}}))["ref"]
    self.assertTrue(self.client.query(query.identify(instance_ref, "sekrit")))

  def test_identity_has_identity(self):
    instance_ref = self.client.query(
      query.create(self.collection_ref, {"credentials": {"password": "sekrit"}}))["ref"]
    secret = self.client.query(
      query.login(instance_ref, {"password": "sekrit"}))["secret"]
    instance_client = self.client.new_session_client(secret=secret)

    self.assertTrue(instance_client.query(query.has_identity()))
    self.assertEqual(instance_client.query(query.identity()), instance_ref)

  #endregion

  #region String functions

  def test_concat(self):
    self.assertEqual(self._q(query.concat(["a", "b", "c"])), "abc")
    self.assertEqual(self._q(query.concat([])), "")
    self.assertEqual(self._q(query.concat(["a", "b", "c"], ".")), "a.b.c")

  def test_casefold(self):
    self.assertEqual(self._q(query.casefold("Hen Wen")), "hen wen")

    # https://unicode.org/reports/tr15/
    self.assertEqual(self._q(query.casefold(u'\u212B', "NFD")), u'A\u030A')
    self.assertEqual(self._q(query.casefold(u'\u212B', "NFC")), u'\u00C5')
    self.assertEqual(self._q(query.casefold(u'\u1E9B\u0323', "NFKD")), u'\u0073\u0323\u0307')
    self.assertEqual(self._q(query.casefold(u'\u1E9B\u0323', "NFKC")), u'\u1E69')

    self.assertEqual(self._q(query.casefold(u'\u212B', "NFKCCaseFold")), u'\u00E5')

  def test_ngram(self):
    self.assertEqual(self._q(query.ngram("what")), ["w", "wh", "h", "ha", "a", "at", "t"])
    self.assertEqual(self._q(query.ngram("what", min=2, max=3)), ["wh", "wha", "ha", "hat", "at"])

    self.assertEqual(
      self._q(query.ngram(["john", "doe"])),
      ["j", "jo", "o", "oh", "h", "hn", "n", "d", "do", "o", "oe", "e"]
    )
    self.assertEqual(
      self._q(query.ngram(["john", "doe"], min=3, max=4)),
      ["joh", "john", "ohn", "doe"]
    )

  def test_findstr(self):
    self.assertEqual(self._q(query.find_str("ABC","A")), 0)
    self.assertEqual(self._q(query.find_str("ABC","A",0)), 0)
    self.assertEqual(self._q(query.find_str("ABC","A",1)), -1)
    self.assertEqual(self._q(query.find_str("a big apple","a", 2)), 6)

  def test_findstrregex(self):
    self.assertEqual(self._q(query.find_str_regex("ABC","A")),[ { "start": 0, "end": 0, "data": 'A' } ])
    self.assertEqual(self._q(query.find_str_regex("ABCAB","AB")),
                          [
                          { 'start': 0, 'end': 1, 'data': 'AB' } ,
                          { 'start': 3, 'end': 4, 'data': 'AB' }
                          ]
                        )
    self.assertEqual(self._q(query.find_str_regex("one fish two Fish","[fF]ish")),
                          [
                          { 'start': 4, 'end': 7, 'data': 'fish' } ,
                          { 'start': 13, 'end': 16, 'data': 'Fish' }
                          ]
    )

  def test_length(self):
    self.assertEqual(self._q(query.length("")), 0)
    self.assertEqual(self._q(query.length("A")), 1)
    self.assertEqual(self._q(query.length("ApPle")), 5)
    self.assertEqual(self._q(query.length("two words")), 9)

  def test_lowercase(self):
    self.assertEqual(self._q(query.lowercase("")), "")
    self.assertEqual(self._q(query.lowercase("A")), "a")
    self.assertEqual(self._q(query.lowercase("ApPle")), 'apple')

  def test_ltrim(self):
    self.assertEqual(self._q(query.ltrim("")), "")
    self.assertEqual(self._q(query.ltrim("    A")), "A")
    self.assertEqual(self._q(query.ltrim("\t\n\t\n  Apple")), 'Apple')
    self.assertEqual(self._q(query.ltrim(" A B C")), "A B C")

  def test_repeat(self):
    self.assertEqual(self._q(query.repeat("A")), "AA")
    self.assertEqual(self._q(query.repeat("ABC", 3)), "ABCABCABC")

  def test_replacestr(self):
    self.assertEqual(self._q(query.replace_str("ABCDE","AB","AA")), "AACDE")
    self.assertEqual(self._q(query.replace_str("One Fish Two Fish","Fish","Cat")), "One Cat Two Cat")

  def test_replacestrregex(self):
    self.assertEqual(self._q(query.replace_str_regex("ABCDE","AB","AA")), "AACDE")
    self.assertEqual(self._q(query.replace_str_regex("One Fish Two fish","[Ff]ish","Cat")), "One Cat Two Cat")

  def test_rtrim(self):
    self.assertEqual(self._q(query.rtrim("A\t\n   ")), "A")
    self.assertEqual(self._q(query.rtrim("ABC DE F ")), "ABC DE F")

  def test_space(self):
    self.assertEqual(self._q(query.space(0)), "")
    self.assertEqual(self._q(query.space(5)), "     ")

  def test_substring(self):
    self.assertEqual(self._q(query.substring("ABCDEF",-3)), "DEF")
    self.assertEqual(self._q(query.substring("ABCDEF",0,3)), "ABC")

  def test_titlecase(self):
    self.assertEqual(self._q(query.titlecase("one fISH tWo FISH")), "One Fish Two Fish")
    self.assertEqual(self._q(query.titlecase("ABC DEF")), "Abc Def")

  def test_trim(self):
    self.assertEqual(self._q(query.trim("   A   ")), "A")
    self.assertEqual(self._q(query.trim("\t\nABC DEF\t\n   ")), "ABC DEF")

  def test_uppercase(self):
    self.assertEqual(self._q(query.uppercase("a")), "A")
    self.assertEqual(self._q(query.uppercase("abc def")), "ABC DEF")

  #endregion

  #region Time and date functions

  def test_time(self):
    time = "1970-01-01T00:00:00.123456789Z"
    self.assertEqual(self._q(query.time(time)), FaunaTime(time))

    # "now" refers to the current time.
    self.assertIsInstance(self._q(query.time("now")), FaunaTime)

  def test_epoch(self):
    self.assertEqual(self._q(query.epoch(12, "second")), FaunaTime("1970-01-01T00:00:12Z"))
    nano_time = FaunaTime("1970-01-01T00:00:00.123456789Z")
    self.assertEqual(self._q(query.epoch(123456789, "nanosecond")), nano_time)

  def test_date(self):
    self.assertEqual(self._q(query.date("1970-01-01")), date(1970, 1, 1))

  #endregion

  #region Miscellaneous functions

  def test_new_id(self):
    self.assertIsNotNone(self._q(query.new_id()))

  def test_database(self):
    self.assertEqual(self._q(query.database("db-name")), Ref("db-name", Native.DATABASES))

  def test_index(self):
    self.assertEqual(self._q(query.index("idx-name")), Ref("idx-name", Native.INDEXES))

  def test_collection(self):
    self.assertEqual(self._q(query.collection("cls-name")), Ref("cls-name", Native.COLLECTIONS))

  def test_function(self):
    self.assertEqual(self._q(query.function("fn-name")), Ref("fn-name", Native.FUNCTIONS))

  def test_role(self):
    self.assertEqual(self._q(query.role("role-name")), Ref("role-name", Native.ROLES))

  def test_equals(self):
    self.assertTrue(self._q(query.equals(1, 1, 1)))
    self.assertFalse(self._q(query.equals(1, 1, 2)))
    self.assertTrue(self._q(query.equals(1)))
    self._assert_bad_query(query.equals())

  def test_contains(self):
    obj = {"a": {"b": 1}}
    self.assertTrue(self._q(query.contains(["a", "b"], obj)))
    self.assertTrue(self._q(query.contains("a", obj)))
    self.assertFalse(self._q(query.contains(["a", "c"], obj)))

  def test_select(self):
    obj = {"a": {"b": 1}}
    self.assertEqual(self._q(query.select("a", obj)), {"b": 1})
    self.assertEqual(self._q(query.select(["a", "b"], obj)), 1)
    self.assertIsNone(self._q(query.select_with_default("c", obj, None)))
    self.assertRaises(NotFound, lambda: self._q(query.select("c", obj)))

  def test_select_all(self):
    self.assertEqual(
      self._q(query.select_all("foo", [{"foo": "bar"}, {"foo": "baz"}])),
      ["bar", "baz"]
    )

    self.assertEqual(
      self._q(query.select_all(["foo", 0], [{"foo": [0, 1]}, {"foo": [2, 3]}])),
      [0, 2]
    )

  def test_select_array(self):
    arr = [1, 2, 3]
    self.assertEqual(self._q(query.select(2, arr)), 3)
    self.assertRaises(NotFound, lambda: self._q(query.select(3, arr)))

  def test_add(self):
    self.assertEqual(self._q(query.add(2, 3, 5)), 10)
    self._assert_bad_query(query.add())

  def test_multiply(self):
    self.assertEqual(self._q(query.multiply(2, 3, 5)), 30)
    self._assert_bad_query(query.multiply())

  def test_subtract(self):
    self.assertEqual(self._q(query.subtract(2, 3, 5)), -6)
    self.assertEqual(self._q(query.subtract(2)), 2)
    self._assert_bad_query(query.subtract())

  def test_divide(self):
    self.assertEqual(self._q(query.divide(2.0, 3, 5)), 2 / 15)
    self.assertEqual(self._q(query.divide(2)), 2)
    self._assert_bad_query(query.divide(1, 0))
    self._assert_bad_query(query.divide())

  def test_modulo(self):
    self.assertEqual(self._q(query.modulo(5, 2)), 1)
    # This is (15 % 10) % 2
    self.assertEqual(self._q(query.modulo(15, 10, 2)), 1)
    self.assertEqual(self._q(query.modulo(2)), 2)
    self._assert_bad_query(query.modulo(1, 0))
    self._assert_bad_query(query.modulo())

  def test_lt(self):
    self.assertTrue(self._q(query.lt(1, 2)))

  def test_lte(self):
    self.assertTrue(self._q(query.lte(1, 1)))

  def test_gt(self):
    self.assertTrue(self._q(query.gt(2, 1)))

  def test_gte(self):
    self.assertTrue(self._q(query.gte(1, 1)))

  def test_and(self):
    self.assertFalse(self._q(query.and_(True, True, False)))
    self.assertTrue(self._q(query.and_(True, True, True)))
    self.assertTrue(self._q(query.and_(True)))
    self.assertFalse(self._q(query.and_(False)))
    self._assert_bad_query(query.and_())

  def test_or(self):
    self.assertTrue(self._q(query.or_(False, False, True)))
    self.assertFalse(self._q(query.or_(False, False, False)))
    self.assertTrue(self._q(query.or_(True)))
    self.assertFalse(self._q(query.or_(False)))
    self._assert_bad_query(query.or_())

  def test_not(self):
    self.assertFalse(self._q(query.not_(True)))
    self.assertTrue(self._q(query.not_(False)))

  def test_to_string(self):
    self.assertEqual(self._q(query.to_string(42)), "42")

  def test_to_number(self):
    self.assertEqual(self._q(query.to_number("42")), 42)

  def test_to_time(self):
    time = "1970-01-01T00:00:00Z"
    self.assertEqual(self._q(query.to_time(time)), FaunaTime(time))

  def test_to_seconds(self):
    expected = (0)
    self.assertEqual(self._q(query.to_seconds(query.epoch(0, "second"))), expected)

  def test_to_millis(self):
    expected = 1552733214259000
    self.assertEqual(self._q(query.to_millis(query.epoch(1552733214259, "second"))), expected)

  def test_to_micros(self):
    expected = 1552733214259000000
    self.assertEqual(self._q(query.to_micros(query.epoch(1552733214259, "second"))), expected)

  def test_day_of_year(self):
    now = datetime.now()
    self.assertEqual(self._q(query.day_of_year(query.time(now.isoformat() + 'Z'))), now.timetuple().tm_yday)

  def test_day_of_month(self):
    now = datetime.now()
    self.assertEqual(self._q(query.day_of_month(query.time(now.isoformat() + 'Z'))), now.day)

  def test_day_of_week(self):
    now = datetime.now()
    self.assertEqual(self._q(query.day_of_week(query.time(now.isoformat() + 'Z'))), now.weekday()+1)

  def test_year(self):
    now = datetime.now()
    self.assertEqual(self._q(query.year(query.time(now.isoformat() + 'Z'))), now.year)

  def test_month(self):
    now = datetime.now()
    self.assertEqual(self._q(query.month(query.time(now.isoformat() + 'Z'))), now.month)

  def test_hour(self):
    expected = 0
    self.assertEqual(self._q(query.hour(query.epoch(0, "second"))), expected)

  def test_minute(self):
    now = datetime.now()
    self.assertEqual(self._q(query.minute(query.time(now.isoformat() + 'Z'))), now.minute)

  def test_second(self):
    now = datetime.now()
    self.assertEqual(self._q(query.second(query.time(now.isoformat() + 'Z'))), now.second)
  
  def test_to_date(self):
    self.assertEqual(self._q(query.to_date("1970-01-01")), date(1970, 1, 1))

  #endregion

  #region Helpers tests

  def test_object(self):
    self.assertEqual(self._q({"x": query.let({"x": 1}, query.var("x"))}), {"x": 1})

  def test_varargs(self):
    # Works for lists too
    self.assertEqual(self._q(query.add([2, 3, 5])), 10)
    # Works for a variable equal to a list
    self.assertEqual(self._q(query.let({"x": [2, 3, 5]}, query.add(query.var("x")))), 10)

  #endregion

  #region Recursive references

  def test_nested_references(self):
    client1 = self.create_new_database(self.admin_client, "parent-database")
    client2 = self.create_new_database(client1, "child-database")

    client2.query(query.create_collection({"name": "a_collection"}))
    client2.query(query.create_role({"name": "a_role", "privileges":{"resource":query.collections(), "actions": {"read": True}}}))

    nested_database_ref = query.database("child-database", query.database("parent-database"))
    nested_collection_ref = query.collection("a_collection", nested_database_ref)
    nested_role_ref = query.role("a_role", nested_database_ref)

    self.assertEqual(self.admin_client.query(query.exists(nested_collection_ref)), True)
    self.assertEqual(self.admin_client.query(query.exists(nested_role_ref)), True)

    parent_db_ref = Ref("parent-database", Native.DATABASES)
    child_db_ref = Ref("child-database", Native.DATABASES, parent_db_ref)

    self.assertEqual(self.admin_client.query(query.paginate(query.collections(nested_database_ref)))["data"],
                     [Ref("a_collection", Native.COLLECTIONS, child_db_ref)])

    self.assertEqual(self.admin_client.query(query.paginate(query.roles(nested_database_ref)))["data"],
                     [Ref("a_role", Native.ROLES, child_db_ref)])

  def test_nested_keys(self):
    client = self.create_new_database(self.admin_client, "db-for-keys")
    client.query(query.create_database({"name": "db-test"}))

    server_key = client.query(query.create_key({
      "database": query.database("db-test"),
      "role": "server"
    }))

    admin_key = client.query(query.create_key({
      "database": query.database("db-test"),
      "role": "admin"
    }))

    self.assertEqual(
      client.query(query.paginate(query.keys()))["data"],
      [server_key["ref"], admin_key["ref"]]
    )

    self.assertEqual(
      self.admin_client.query(query.paginate(query.keys(query.database("db-for-keys"))))["data"],
      [server_key["ref"], admin_key["ref"]]
    )

  def create_new_database(self, client, name):
    client.query(query.create_database({"name": name}))
    key = client.query(query.create_key({"database": query.database(name), "role": "admin"}))
    return client.new_session_client(secret=key["secret"])

  #endregion

  def test_equality(self):
    self.assertEqual(query.var("x"), _Expr({"var": "x"}))
    self.assertEqual(query.match(Ref("widgets_by_name", Native.INDEXES), "computer"),
                     _Expr({"match": Ref("widgets_by_name", Native.INDEXES), "terms": "computer"}))

  def test_repr(self):
    self.assertRegexCompat(repr(query.var("x")), r"Expr\({u?'var': u?'x'}\)")
    self.assertRegexCompat(repr(Ref("collections")), r"Ref\(id=collections\)")
    self.assertRegexCompat(repr(SetRef(query.match(query.index("widgets")))),
                           r"SetRef\({u?'match': Expr\({u?'index': u?'widgets'}\)}\)")
