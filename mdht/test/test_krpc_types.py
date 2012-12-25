from twisted.trial import unittest

from mdht.krpc_types import _KRPC, Query, Response, Error

class KRPCTestCase(unittest.TestCase):
    def test_build_repr_empty(self):
        k = _KRPC()
        self.assertEquals("", k._build_repr([]))

    def test_build_repr_setTransactionID(self):
        k = _KRPC()
        k._transaction_id = 109825
        self.assertEquals("_transaction_id=109825",
                            k._build_repr(["_transaction_id"]))

class QueryTestCase(unittest.TestCase):
    def setUp(self):
        self.q = Query()
        self.q._transaction_id = 500
        self.q._from = 27
        self.q.rpctype = "ping"

    def test_build_response(self):
        nodes = None
        token = 8192
        peers = None
        r = self.q.build_response(nodes, token, peers)
        q = self.q
        expected_r = Response(_transaction_id=q._transaction_id,
                rpctype=q.rpctype, nodes=nodes, token=token, peers=peers)
        self.assertEquals(expected_r, r)

    def test_build_error(self):
        code = 203
        message = "Oops, error"
        e = self.q.build_error(code, message)
        q = self.q
        expected_e = Error(_transaction_id=q._transaction_id,
                code=code, message=message)
        self.assertEquals(expected_e, e)

    def test_repr(self):
        expected_repr = "<Query: _transaction_id=500 rpctype=ping _from=27>"
        self.assertEquals(expected_repr, repr(self.q))

    def test__eq__(self):
        q1, q2 = self._gen_equal_announce_peers()
        self.assertEquals(q1, q2)

    def test__ne___(self):
        q1, q2 = self._gen_equal_announce_peers()
        q1._transaction_id = 88
        q2._transaction_id = 66
        self.assertNotEquals(q1, q2)

    def _gen_equal_announce_peers(self):
        q1 = Query()
        q2 = Query()
        q1._transaction_id = q2._transaction_id = 99
        q1._from = q2._from = 55
        q1.rpctype = q2.rpctype = "announce_peer"
        q1.token = q2.token = 13
        q1.port = q2.port = 123
        q1.target_id = q2.target_id = 66
        self.assertEquals(q1, q2)
        return (q1, q2)


class ResponseTestCase(unittest.TestCase):

    def setUp(self):
        r = Response()
        r2 = Response()
        r2._transaction_id = r._transaction_id = 18095
        r2._from = r._from = 15
        r2.token = r.token = 1980
        self.r = r
        self.r2 = r2

    def test_repr(self):
        expected_repr = "<Response: _transaction_id=18095 _from=15 token=1980>"
        self.assertEquals(expected_repr, str(self.r))

    def test__eq__(self):
        self.assertEquals(self.r, self.r2)

    def test__ne__(self):
        self.r._from = 1111
        self.r2._from = 5555
        self.assertNotEquals(self.r, self.r2)

class ErrorTestCase(unittest.TestCase):
    def test_repr(self):
        e = Error()
        e._transaction_id = 222
        e.code = 202
        e.message = "Invalid Query"
        expected_repr = ("<Error: _transaction_id=222 " +
                         "code=202 message='Invalid Query'>")
        self.assertEquals(expected_repr, repr(e))
