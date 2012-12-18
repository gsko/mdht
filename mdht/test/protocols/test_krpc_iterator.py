from twisted.trial import unittest
from twisted.internet import defer
from twisted.python.monkey import MonkeyPatcher

from mdht.contact import Node
from mdht.kademlia.routing_table import TreeRoutingTable
from mdht.protocols.krpc_iterator import KRPC_Iterator, IterationError
# Imported so that the reactor can be patched out
from mdht.protocols import krpc_sender
from mdht.krpc_types import Response
from mdht.protocols.errors import TimeoutError

from mdht.test.utils import Counter, HollowTransport, HollowReactor

make_node = lambda num: Node(num, ("127.0.0.1", num))
make_peer = lambda num: ("127.0.0.1", num)

# Make 65535 nodes for testing
test_nodes = [make_node(num) for num in range(1, 2**16)]
test_peers = [make_peer(num) for num in range(1, 2**16)]

class HollowKRPC_Responder(object):
    """
    Hollowed out KRPC_Responder for testing KRPC_Iterator
    """
    def __init__(self):
        self.node_id = 999
        self.routing_table = TreeRoutingTable(self.node_id)
        self.find_node_count = 0
        self.get_peers_count = 0
        self.defer_gen = defer.Deferred

    def find_node(self, address, node_id, timeout=None):
        self.find_node_count += 1
        return defer_gen()

    def get_peers(self, address, infohash, timeout=None):
        self.get_peers_count += 1
        return defer_gen()

class DeferredGrabber(object):
    """
    Wrap over sendQuery, recording its arguments/results
    """
    def __init__(self, sendQuery):
        self.sendQuery = sendQuery
        self.deferreds = []
    
    def __call__(self, query, address, timeout=None):
        deferred = self.sendQuery(query, address, timeout)
        # Store the original query and the resulting deferred
        self.deferreds.append((query, deferred))
        return deferred

class KRPC_Iterator_TestCase(unittest.TestCase):
    def setUp(self):
        self.monkey_patcher = MonkeyPatcher()
        self.monkey_patcher.addPatch(krpc_sender, "reactor", HollowReactor())
        self.monkey_patcher.patch()
        self.k_iter = KRPC_Iterator()
        self.k_iter.transport = HollowTransport()
        self.target_id = 5

    def tearDown(self):
        self.monkey_patcher.restore()

    #
    # Find iterate test cases 
    #
    def test_find_iterate_properNumberOfQueriesSent_noNodesInRT(self):
        self._check_k_iter_sendsProperNumberOfQueries_noNodesInRT(
                self.k_iter.find_iterate)

    def test_find_iterate_firesAfterAllQueriesFire(self):
        self._check_k_iter_firesAfterAllQueriesFire(
                self.k_iter.find_iterate)

    def test_find_iterate_usesNodesFromRoutingTable(self):
        self._check_k_iter_usesNodesFromRoutingTable(
                self.k_iter.find_iterate)

    def test_find_iterate_noNodesRaisesIterationError(self):
        self._check_k_iter_raisesIterationErrorOnNoSeedNodes(
                self.k_iter.find_iterate)

    def test_find_iterate_allQueriesTimeoutRaisesIterationError(self):
        self._check_k_iter_failsWhenAllQueriesTimeOut(
                self.k_iter.find_iterate)

    def test_find_iterate_returnsNewNodes(self):
        # deferreds is a (query, deferred) tuple list
        (deferreds, d) = self._iterate_and_returnQueriesAndDeferreds(
                self.k_iter.find_iterate)
        num_queries = len(deferreds)
        # Use any nodes as result nodes (even the nodes themselves)
        result_nodes = test_nodes[:num_queries]
        # Set up dummy node_id's
        node_id = 1
        for (query, deferred), node in zip(deferreds, result_nodes):
            response = query.build_response(nodes=[node])
            response._from = node_id
            node_id += 1
            deferred.callback(response)
        expected_nodes = set(result_nodes)
        d.addErrback(self._fail_errback)
        d.addCallback(self._compare_nodes, expected_nodes)
        # Make sure we don't accidentally slip past an
        # uncalled deferred
        self.assertTrue(d.called)

    #
    # Get iterate test cases
    #
    def test_get_iterate_properNumberOfQueriesSent_noNodesInRT(self):
        self._check_k_iter_sendsProperNumberOfQueries_noNodesInRT(
                self.k_iter.get_iterate)

    def test_get_iterate_firesAfterAllQueriesFire(self):
        self._check_k_iter_firesAfterAllQueriesFire(
                self.k_iter.get_iterate)

    def test_get_iterate_usesNodesFromRoutingTable(self):
        self._check_k_iter_usesNodesFromRoutingTable(
                self.k_iter.get_iterate)

    def test_get_iterate_noNodesRaisesIterationError(self):
        self._check_k_iter_raisesIterationErrorOnNoSeedNodes(
                self.k_iter.get_iterate)

    def test_get_iterate_allQueriesTimeoutRaisesIterationError(self):
        self._check_k_iter_failsWhenAllQueriesTimeOut(
                self.k_iter.get_iterate)

    def test_get_iterate_returnsNewNodesAndPeers(self):
        # deferreds is a (query, deferred) tuple list
        # where each tuple corresponds to one outbound query
        # and deferred result
        #
        # and d is a deferred result of the iter_func
        (deferreds, d) = self._iterate_and_returnQueriesAndDeferreds(
                self.k_iter.get_iterate)
        num_queries = len(deferreds)

        # Use any nodes as result nodes (even the nodes themselves)
        result_nodes = test_nodes[:num_queries]
        result_peers = test_peers[:num_queries]

        # Set up dummy node_id's
        node_id = 1

        # Simulate the event that every outbound
        # query received a result (by making dummy valid
        # responses and feeding them into the deferred)
        for (query, deferred), node, peer in \
            zip(deferreds, result_nodes, result_peers):
            response = query.build_response(nodes=[node], peers=[peer])
            response._from = node_id
            node_id += 1
            deferred.callback(response)

        expected_nodes = result_nodes
        expected_peers = result_peers
        d.addErrback(self._fail_errback)
        d.addCallback(self._compare_peers, expected_peers)
        d.addCallback(self._compare_nodes, expected_nodes)
        # Make sure we don't accidentally slip past an
        # uncalled deferred
        self.assertTrue(d.called)

    # Auxilary test functions
    # that are generalizations of the test
    # cases below
    def _check_k_iter_sendsProperNumberOfQueries_noNodesInRT(self, iter_func):
        sendQuery = self.k_iter.sendQuery
        self.k_iter.sendQuery = Counter(sendQuery)
        expected_num_queries = 15
        iter_func(self.target_id, test_nodes[:expected_num_queries])
        self.assertEquals(expected_num_queries, self.k_iter.sendQuery.count)

    def _check_k_iter_firesAfterAllQueriesFire(self, iter_func):
        """
        Ensure one 'iterative' query fires after all its subqueries fire
        """
        sendQuery = self.k_iter.sendQuery
        self.k_iter.sendQuery = DeferredGrabber(sendQuery)
        num_queries = 5
        d = iter_func(self.target_id, test_nodes[:num_queries])
        deferreds = self.k_iter.sendQuery.deferreds
        test_node_id = 1
        # Make sure that `num_queries` queries were sent
        self.assertEquals(num_queries, len(deferreds))
        for (query, deferred) in deferreds:
            # Grab any node as a response node
            nodes = [test_nodes[55]]
            # Make a valid response node to feed
            # into the subdeferreds
            response = query.build_response(nodes=nodes)
            # Any node id works
            response._from = test_node_id
            test_node_id += 1
            if query.rpctype == "get_peers":
                response.token = 555
            deferred.callback(response)
        # After "receiving a response" to every outgoing
        # query, our main deferred should fire
        self.assertTrue(d.called)

    def _check_k_iter_usesNodesFromRoutingTable(self, iter_func):
        get_closest_nodes = self.k_iter.routing_table.get_closest_nodes
        self.k_iter.routing_table.get_closest_nodes = \
            Counter(get_closest_nodes)
        # If we dont supply any testing nodes,
        # the protocol should check its routingtable
        d = iter_func(self.target_id)
        d.addErrback(self._silence_iteration_error)
        looked_for_nodes = \
                self.k_iter.routing_table.get_closest_nodes.count > 0
        self.assertTrue(looked_for_nodes)

    def _check_k_iter_raisesIterationErrorOnNoSeedNodes(self, iter_func):
        d = iter_func(self.target_id)
        d.addCallbacks(callback=self._ensure_iteration_error_callback,
                errback=self._ensure_iteration_error_errback)

    def _ensure_iteration_error_errback(self, failure):
        isnt_iteration_error = failure.check(IterationError) is None
        if isnt_iteration_error:
            self.fail("KRPC_Iterator threw an error that wasn't " +
                    "an IterationError")

    def _ensure_iteration_error_callback(self, _ignored_result):
        self.fail("KRPC_Iterator did not throw an IterationError " +
                "and was incorrectly successful instead")

    def _check_k_iter_failsWhenAllQueriesTimeOut(self, iter_func):
        sendQuery = self.k_iter.sendQuery
        self.k_iter.sendQuery = DeferredGrabber(sendQuery)
        num_queries = 5
        d = iter_func(self.target_id, test_nodes[:num_queries])
        deferreds = self.k_iter.sendQuery.deferreds

        # Make sure an IterationError is thrown once we
        # artificially timeout all queries
        d.addCallbacks(callback=self._ensure_iteration_error_callback,
                errback=self._ensure_iteration_error_errback)

        # Timeout all queries
        for (query, deferred) in deferreds:
            deferred.errback(TimeoutError())
        
    def _compare_nodes(self, result_node_list, expected_nodes):
        # Assert that our resulting list of nodes
        # matches what we expected
        for node in result_node_list:
            self.assertTrue(node in expected_nodes)
        self.assertEquals(len(expected_nodes),
                len(result_node_list))

    def _compare_peers(self, result, expected_peers):
        (result_nodes, result_peers) = result
        self.assertEquals(set(expected_peers), set(result_peers))
        # Return the nodes, since the next callback
        # will check the expected nodes
        return result_nodes

    def _fail_errback(self, failure):
        exception = failure.value
        self.fail("KRPC_Iterator failed when it shouldn't have: " 
                + str(exception))

    def _iterate_and_returnQueriesAndDeferreds(self, iter_func):
        # Capture all outbound queries
        # and all deferreds
        sendQuery = self.k_iter.sendQuery
        self.k_iter.sendQuery = DeferredGrabber(sendQuery)
        # Use the first 10 nodes as our seeds
        d = iter_func(self.target_id, test_nodes[:10])
        deferreds = self.k_iter.sendQuery.deferreds
        return (deferreds, d)

    def _silence_iteration_error(self, failure):
        failure.trap(IterationError)
