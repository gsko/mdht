from twisted.trial import unittest
from twisted.internet import defer

from mdht.coding import krpc_coder
from mdht.contact import Node
from mdht.protocols.krpc_simple import LiveResult, LiveResultError, KRPC_Simple
from mdht.test.utils import test_nodes, HollowTransport

TEST_NODE_ID = 5
TEST_PORT = 10

class LiveResult_TestCase(unittest.TestCase):
    def test_add_result_IncreasesResultSize(self):
        live_result = LiveResult()
        results = live_result.get_results()
        self.assertEquals(0, len(results))
        live_result.add_results([5])
        results = live_result.get_results()
        self.assertEquals(1, len(results))

    def test_add_results_noMoreResultsAcceptedAfterComplete(self):
        live_result = LiveResult()
        live_result.mark_completed()
        self.assertRaises(LiveResultError, live_result.add_results, [1,2])

    def _listener(self):
        self.call_count += 1

    def test_register_listener_FiresListenerOnAdd(self):
        self.call_count = 0
        live_result = LiveResult()
        live_result.register_listener(self._listener)
        live_result.add_results([1,2,3,4])
        self.assertEquals(1, self.call_count)

    def test_register_listener_FiresListenerOnCompletion(self):
        self.call_count = 0
        live_result = LiveResult()
        live_result.register_listener(self._listener)
        live_result.add_results([99,100])
        live_result.mark_completed()
        # one call for results,
        # one call for completion
        self.assertEquals(2, self.call_count)

    def test_mark_completed_SetsFlag(self):
        live_result = LiveResult()
        live_result.mark_completed()
        self.assertTrue(live_result.is_complete)

class KRPC_Simple_TestCase(unittest.TestCase):
    def setUp(self):
        self.ksimple = KRPC_Simple(TEST_NODE_ID)
        self.ksimple.transport = HollowTransport()

    def _grab_outbound_krpc(self):
        krpc_msg = self.ksimple.transport.packet
        self.assertNotEquals(None, krpc_msg)
        krpc = krpc_coder.decode(krpc_msg)
        return krpc

    def test_get_liveResultGrowsWithSingleResponse(self):
        self._prepare_proto()
        
        live_result = self.ksimple.get(890)
        krpc = self._grab_outbound_krpc()
        # any address tuple will do as a result_peer
        result_peer = test_nodes[1].node_address
        response = krpc.build_response(peers=[result_peer])
        self._encode_and_respond(response)
        results = live_result.get_results()
        self.assertEquals(1, len(results))
        expected_result = (responding_node, result_peer)
        for result in results:
            self.assertEquals(expected_result, result)
            break

    def test_get_liveResultDoesntGrowWithError(self):
        self._prepare_proto()

        live_result = self.ksimple.get(890)
        krpc = self._grab_outbound_krpc()
        # any address tuple will do as a result_peer
        error = krpc.build_error()
        responding_node = self._encode_and_respond(error)
        results = live_result.get_results()
        self.assertEquals(0, len(results))

    def test_put(self):
        self.assertTrue(False)

    def _encode_and_respond(self, krpc):
        krpc._from = 123
        encoded_krpc = krpc_coder.encode(krpc)
        responding_node = test_nodes[22]
        self.ksimple.datagramReceived(
            encoded_krpc, responding_node.node_addres)
        return responding_node

    def _prepare_proto(self):
        # prepare proto for search
        seed_node = test_nodes[0]
        node_accepted = self.ksimple.routing_table.offer_node(seed_node)
        self.assertTrue(node_accepted)
