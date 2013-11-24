from twisted.trial import unittest
from twisted.python.monkey import MonkeyPatcher

from mdht.krpc_types import Query, Response, Error
from mdht.kademlia.routing_table import TreeRoutingTable
from mdht.protocols import krpc_sender
from mdht.protocols.krpc_sender import KRPC_Sender
from mdht.protocols.errors import TimeoutError
from mdht.coding import krpc_coder
from mdht.test.utils import Clock, HollowReactor, HollowTransport, Counter

# Write two functions that simply remove / restore
# the reactor for krpc_sender
monkey_patcher = MonkeyPatcher()

def _swap_out_reactor():
    monkey_patcher.addPatch(krpc_sender, "reactor", HollowReactor())
    monkey_patcher.patch()

def _restore_reactor():
    monkey_patcher.restore()

# Arguments for the sendQuery
timeout = 15
address = ("127.0.0.1", 2828)

class KRPC_Sender_ReceivedCallChainTestCase(unittest.TestCase):
    def _patch_counter_and_input_krpc(self, krpc, method_name,
                                      num_calls=1, address=None):
        if address is None:
            address = ("127.0.0.1", 8888)
        k_messenger = KRPC_Sender(TreeRoutingTable, 2**50)
        # Patch in our counter
        counter = Counter()
        setattr(k_messenger, method_name, counter)

        # Pass in the krpc
        k_messenger.datagramReceived(krpc_coder.encode(krpc), address)
        self.assertEquals(num_calls, counter.count)

    def setUp(self):
        _swap_out_reactor()

        q = Query()
        q._transaction_id = 50
        q._from = 58
        q.rpctype = "ping"
        self.query = q

    def tearDown(self):
        _restore_reactor()

    def test_krpcReceived(self):
        self._patch_counter_and_input_krpc(self.query, "krpcReceived")

    def test_queryReceived(self):
        self._patch_counter_and_input_krpc(self.query, "queryReceived")

    def test_ping_Received(self):
        self._patch_counter_and_input_krpc(
                self.query, self.query.rpctype + "_Received")

    def test_find_node_Received(self):
        self.query.rpctype = "find_node"
        self.query.target_id = 1500

        self._patch_counter_and_input_krpc(
                self.query, self.query.rpctype + "_Received")

    def test_get_peers_Received(self):
        self.query.rpctype = "get_peers"
        self.query.target_id = 1500
        self._patch_counter_and_input_krpc(
                self.query, self.query.rpctype + "_Received")

    def test_announce_peer_Received(self):
        q = self.query
        q.rpctype = "announce_peer"
        q.target_id = 1500
        q.port = 5125
        q.token = 15
        self._patch_counter_and_input_krpc(
                self.query, self.query.rpctype + "_Received")

    def test_responseReceived(self):
        # Make a query that we will "send"
        query = Query()
        query.rpctype = "ping"
        # Make the protocol and patch in our counter, transport, and reactor
        counter = Counter()
        k_messenger = KRPC_Sender(TreeRoutingTable, 2**50)
        k_messenger.transport = HollowTransport()
        k_messenger.responseReceived = counter
        # Send the query and receive the response
        k_messenger.sendQuery(query, address, timeout)
        self.assertTrue(query._transaction_id in k_messenger._transactions)
        # Make a response that we will "receive"
        response = query.build_response()
        response._from = 9
        k_messenger.datagramReceived(krpc_coder.encode(response), address)
        _restore_reactor()
        self.assertEquals(1, counter.count)

class KRPC_Sender_DeferredTestCase(unittest.TestCase):
    def setUp(self):
        _swap_out_reactor()
        self.k_messenger = KRPC_Sender(TreeRoutingTable, 2**50)
        self.k_messenger.transport = HollowTransport()
        self.query = Query()
        self.query.rpctype = "ping"

    def tearDown(self):
        _restore_reactor()

    def _response_equality(self, response, expected_response):
            self.assertEquals(expected_response._transaction_id,
                response._transaction_id)
            self.assertEquals(expected_response._from,
                response._from)
            return response

    def test_callback(self):
        counter = Counter()
        d = self.k_messenger.sendQuery(self.query, address, timeout)
        self.assertTrue(self.query._transaction_id in
                        self.k_messenger._transactions)
        # Build the response we will "receive"
        response = self.query.build_response()
        response._from = 9
        d.addCallback(self._response_equality, response)
        d.addCallback(counter)
        encoded_response = krpc_coder.encode(response)
        self.k_messenger.datagramReceived(encoded_response, address)
        self.assertEquals(1, counter.count)
        self.assertFalse(self.query._transaction_id in
                         self.k_messenger._transactions)

    def _error_equality(self, error, expected_error):
                self.assertEquals(expected_error._transaction_id,
                                  error._transaction_id)
                self.assertEquals(expected_error.code, error.code)
                return error 

    def test_errback_KRPCError(self):
        counter = Counter()
        d = self.k_messenger.sendQuery(self.query, address, timeout)
        self.assertTrue(self.query._transaction_id in
                        self.k_messenger._transactions)
        # Build the response we will "receive"
        error = self.query.build_error()
        d.addErrback(self._error_equality, error)
        d.addErrback(counter)
        encoded_error = krpc_coder.encode(error)
        self.k_messenger.datagramReceived(encoded_error, address)
        self.assertEquals(1, counter.count)
        self.assertFalse(self.query._transaction_id in
                         self.k_messenger._transactions)

    def test_errback_InvalidKRPCError(self):
        # Make an invalid query
        query = Query()
        query.rpctype = "pingpong"
        d = self.k_messenger.sendQuery(query, address, timeout)
        self.assertFalse(self.query._transaction_id in
                         self.k_messenger._transactions)

        # Cleanup the error
        d.addErrback(lambda failure: failure.trap(krpc_coder.InvalidKRPCError))

    def test_errback_TimeoutError(self):
        d = self.k_messenger.sendQuery(self.query, address, timeout)
        self.assertTrue(self.query._transaction_id in
                        self.k_messenger._transactions)
        d.errback(TimeoutError())
        self.assertFalse(self.query._transaction_id in
                         self.k_messenger._transactions)

        # Cleanup the error
        d.addErrback(lambda failure: failure.trap(TimeoutError))
