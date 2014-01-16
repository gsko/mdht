from twisted.trial import unittest
from twisted.internet import defer

from mdht.coding import krpc_coder
from mdht.contact import Node
from mdht.protocols.krpc_simple import LiveSearch, LiveSearchError, KRPC_Simple
from mdht.test.utils import test_nodes, HollowTransport, HollowReactor

TEST_NODE_ID = 5
TEST_PORT = 10
TEST_TARGET_ID = 98931616

class LiveSearch_TestCase(unittest.TestCase):
    def test_add_result_IncreasesResultSize(self):
        live_search = LiveSearch(TEST_TARGET_ID)
        results = live_search.get_results()
        self.assertEquals(0, len(results))
        live_search.add_results([5])
        results = live_search.get_results()
        self.assertEquals(1, len(results))

    def test_add_results_noMoreResultsAcceptedAfterComplete(self):
        live_search = LiveSearch(TEST_TARGET_ID)
        live_search.mark_completed()
        self.assertRaises(LiveSearchError, live_search.add_results, [1,2])

    def _listener(self):
        self.call_count += 1

    def test_register_listener_FiresListenerOnAdd(self):
        self.call_count = 0
        live_search = LiveSearch(TEST_TARGET_ID)
        live_search.register_listener(self._listener)
        live_search.add_results([1,2,3,4])
        self.assertEquals(1, self.call_count)

    def test_register_listener_FiresListenerOnCompletion(self):
        self.call_count = 0
        live_search = LiveSearch(TEST_TARGET_ID)
        live_search.register_listener(self._listener)
        live_search.add_results([99,100])
        live_search.mark_completed()
        # one call for results,
        # one call for completion
        self.assertEquals(2, self.call_count)

    def test_mark_completed_SetsFlag(self):
        live_search = LiveSearch(TEST_TARGET_ID)
        live_search.mark_completed()
        self.assertTrue(live_search.is_complete)

class KRPC_Simple_TestCase(unittest.TestCase):
    def setUp(self):
        self.ksimple = KRPC_Simple(TEST_NODE_ID)
        self.ksimple.transport = HollowTransport()
        self.ksimple._reactor = HollowReactor()

    def test_get_liveResultGrowsWithSingleResponse(self):
        seed_node = self._init_seed_node()
        
        live_search = self.ksimple.get(890)
        self.assertTrue(seed_node in live_search.queried_nodes)
        query = self._grab_outbound_get_peers()
        result_peer = test_nodes[33].address
        response = query.build_response(peers=[result_peer])
        responding_node = self._encode_and_respond(response)
        results = live_search.get_results()
        self.assertEquals(1, len(results))
        self.assertTrue(live_search.queried_nodes)
        for result in results:
            self.assertEquals(result_peer, result)
            break
        self.assertTrue(live_search.is_complete)

    def test_get_protoSendsAnotherGetPeersQueryOnResponseWithNodes(self):
        seed_node = self._init_seed_node()
        
        live_search = self.ksimple.get(890)
        self.assertTrue(seed_node in live_search.queried_nodes)
        first_query = self._grab_outbound_get_peers()
        # any address tuple will do as a result_peer
        result_node = test_nodes[1]
        response = first_query.build_response(nodes=[result_node])
        self.assertEquals(0, len(live_search.get_results()))
        self._encode_and_respond(response)
        self.assertFalse(live_search.is_complete)
        self.assertTrue(result_node in live_search.queried_nodes)
        second_query = self._grab_outbound_get_peers()
        self.assertNotEquals(second_query, first_query)
        self.assertFalse(live_search.is_complete)

    def test_get_liveResultDoesntGrowWithError(self):
        seed_node = self._init_seed_node()

        live_search = self.ksimple.get(TEST_TARGET_ID)
        self.assertTrue(seed_node in live_search.queried_nodes)
        query = self._grab_outbound_get_peers()
        error = query.build_error()
        self._encode_and_respond(error)
        results = live_search.get_results()
        self.assertEquals(0, len(results))

    def test_get_completionWithNoPeers(self):
        live_search = self.ksimple.get(TEST_TARGET_ID)
        self.assertEquals(0, len(live_search.get_results()))
        self.assertTrue(live_search.is_complete)

    def test_put(self):
        self.assertTrue(False)

    def _encode_and_respond(self, krpc):
        responding_node = test_nodes[22]
        krpc._from = responding_node.node_id
        encoded_krpc = krpc_coder.encode(krpc)
        self.ksimple.datagramReceived(encoded_krpc, responding_node.address)
        return responding_node

    def _init_seed_node(self):
        # prepare proto for search
        seed_node = test_nodes[0]
        node_accepted = self.ksimple.routing_table.offer_node(seed_node)
        self.assertTrue(node_accepted)
        return seed_node

    def _grab_outbound_get_peers(self):
        encoded_query = self.ksimple.transport.packet
        self.ksimple.transport._reset()
        self.assertNotEquals(None, encoded_query)
        query = krpc_coder.decode(encoded_query)
        self.assertEquals("get_peers", query.rpctype)
        return query 
