from twisted.trial import unittest

from mdht.coding.krpc_coder import (
        encode, decode, _chunkify, _decode_addresses,
        InvalidKRPCError)
from mdht.coding import basic_coder
from mdht.krpc_types import Query, Response, Error
from mdht.contact import Node

encode_and_decode = lambda krpc: decode(encode(krpc))

class QueryCodingTestCase(unittest.TestCase):

    test_target_id = 551232
    test_port = 511
    test_token = 5555

    def setUp(self):
        q = self.q = Query()
        q._transaction_id = 15
        q._from = 2**120

    def test_encode_validPing(self):
        q = self.q
        q.rpctype = "ping"
        encoding = encode(q)
        expected_encoding = ('d1:ad2:id20:\x00\x00\x00\x00\x01\x00\x00' +
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00e1:q4:' +
            'ping1:t1:\x0f1:y1:qe')
        self.assertEquals(expected_encoding, encoding)

    def test_encode_validFindNode(self):
        q = self.q
        q.target_id = self.test_target_id
        q.rpctype = "find_node"
        encoding = encode(q)
        expected_encoding = ('d1:ad2:id20:\x00\x00\x00\x00\x01\x00\x00\x00' +
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x006:target20:' +
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' + 
            '\x00\x00\x08i@e1:q9:find_node1:t1:\x0f1:y1:qe')
        self.assertEquals(expected_encoding, encoding)

    def test_encode_validGetPeers(self):
        q = self.q
        q.target_id = self.test_target_id
        q.rpctype = "get_peers"
        encoding = encode(q)
        expected_encoding = ('d1:ad2:id20:\x00\x00\x00\x00\x01\x00\x00\x00' +
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x009:info_hash' +
            '20:\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            '\x00\x00\x00\x08i@e1:q9:get_peers1:t1:\x0f1:y1:qe')
        self.assertEquals(expected_encoding, encoding)

    def test_encode_validAnnouncePeer(self):
        q = self.q
        q.rpctype = "announce_peer"
        q.target_id = self.test_target_id
        q.port = self.test_port
        q.token = self.test_token
        encoding = encode(q)
        expected_encoding = ('d1:ad2:id20:\x00\x00\x00\x00\x01\x00\x00' +
            '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x009:info_hash' +
            '20:\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
            '\x00\x00\x00\x08i@4:porti511e5:token2:\x15\xb3e1:q13:'+
            'announce_peer1:t1:\x0f1:y1:qe')
        self.assertEquals(expected_encoding, encoding)

    def test_encode_and_decode_validPing(self):
        q = self.q
        q.rpctype = "ping"
        processed_query = encode_and_decode(q)
        self.assertEquals(processed_query, q)

    def test_encode_and_decode_validFindNode(self):
        q = self.q
        q.rpctype = "find_node"
        q.target_id = 2**15
        processed_query = encode_and_decode(q)
        self.assertEquals(processed_query, q)


    def test_encode_and_decode_invalidRPCType(self):
        q = self.q
        q._transaction_id = 2**159
        q._from = 2**120
        q.rpctype = "find_candy"
        q.target_id = 15
        self.assertRaises(InvalidKRPCError, encode_and_decode, q)

    def test_encode_and_decode_invalidTargetID(self):
        q = self.q
        q.rpctype = "find_node"
        q.target_id = 2**160
        self.assertRaises(InvalidKRPCError, encode_and_decode, q)

    def test_encode_and_decode_invalidPort(self):
        q = self.q
        q.rpctype = "announce_peer"
        q.target_id = self.test_target_id
        q.port = 70000
        q.token = self.test_token
        self.assertRaises(InvalidKRPCError, encode_and_decode, q)

class ResponseCodingTestCase(unittest.TestCase):

    # ping and find_node are subsets of get_peers queries
    # so it is enough to test both ping and find_node by using
    # a single get_peers query
    def test_encode_validGetPeersResponseWithPeers(self):
        r = Response()
        r._transaction_id = 1903890316316
        r._from = 169031860931900138093217073128059
        r.token = 90831
        r.peers = [("127.0.0.1", 80), ("4.2.2.1", 8905), ("0.0.0.0", 0),
                    ("255.255.255.255", 65535), ("8.8.8.8", 53)]
        expected_encoding = 'd1:rd2:id20:\x00\x00\x00\x00\x00\x00\x08U{fDA\xb0\x88\xe6\x8a\xec\xf8\xe2{5:token3:\x01b\xcf6:valuesl6:\x7f\x00\x00\x01\x00P6:\x04\x02\x02\x01"\xc96:\x00\x00\x00\x00\x00\x006:\xff\xff\xff\xff\xff\xff6:\x08\x08\x08\x08\x005ee1:t6:\x01\xbbH\xb4\xbc\x1c1:y1:re'
        encoding = encode(r)
        self.assertEquals(expected_encoding, encoding)

    def test_encode_and_decode_validGetPeersResponseWithPeers(self):
        r = Response()
        r._transaction_id = 1903890316316
        r._from = 169031860931900138093217073128059
        r.token = 90831
        r.peers = [("127.0.0.1", 80), ("4.2.2.1", 8905), ("0.0.0.0", 0),
                    ("8.8.8.8", 53), ("255.255.255.255", 65535)]
        processed_response = encode_and_decode(r)
        self.assertEquals(r._transaction_id, processed_response._transaction_id)
        self.assertEquals(r._from, processed_response._from)
        self.assertEquals(r.token, processed_response.token)
        self.assertEquals(r.peers, processed_response.peers)

    def test_encode_validGetPeersResponseWithNodes(self):
        r = Response()
        r._transaction_id = 1903890316316
        r._from = 169031860931900138093217073128059
        r.token = 90831
        r.nodes = [
            Node(2**158, ("127.0.0.1", 890)),
            Node(2**15, ("127.0.0.1", 8890)),
            Node(2**128, ("127.0.0.1", 1890)),
            Node(2**59, ("127.0.0.1", 7890)),
            Node(2**153, ("127.0.0.1", 5830))
        ]
        expected_encoding = ('d1:rd2:id20:\x00\x00\x00\x00\x00\x00\x08' +
                'U{fDA\xb0\x88\xe6\x8a\xec\xf8\xe2{5:nodes130:@\x00\x00\x00' +
                '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
                '\x00\x00\x7f\x00\x00\x01\x03z\x00\x00\x00\x00\x00\x00\x00' +
                '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x80\x00\x7f' +
                '\x00\x00\x01"\xba\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00' +
                '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x7f\x00\x00\x01' +
                '\x07b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08' +
                '\x00\x00\x00\x00\x00\x00\x00\x7f\x00\x00\x01\x1e\xd2\x02' +
                '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
                '\x00\x00\x00\x00\x00\x7f\x00\x00\x01\x16\xc65:token' +
                '3:\x01b\xcfe1:t6:\x01\xbbH\xb4\xbc\x1c1:y1:re')
        encoding = encode(r)
        self.assertEquals(expected_encoding, encoding)

    def test_encode_and_decode_validPingResponse(self):
        r = Response()
        r._transaction_id = 2095
        r._from = 2**15
        processed_response = encode_and_decode(r)
        self.assertEquals(r._transaction_id, processed_response._transaction_id)
        self.assertEquals(r._from, processed_response._from)

class ErrorCodingTestCase(unittest.TestCase):
    def test_encode_and_decode_validError(self):
        e = Error()
        e._transaction_id = 129085
        e.code = 202
        e.message = ""
        processed_error = encode_and_decode(e)
        self.assertEquals(e._transaction_id, processed_error._transaction_id)
        self.assertEquals(e.code, processed_error.code)
        self.assertEquals(e.message, processed_error.message)

    def test_encode_invalidErrorCode(self):
        e = Error()
        e._transaction_id = 9052
        # e.code must be in {201, 202, 203}
        e.code = 512
        e.message = ""
        self.assertRaises(InvalidKRPCError, encode, e)
