"""
@author Greg Skoczek

Module containing an iterative KRPC protocol along with auxilary classes

"""
from zope.interface import implements
from twisted.internet import defer

from mdht.protocols.krpc_responder import KRPC_Responder
from mdht.protocols.errors import TimeoutError, KRPCError

class IterationError(Exception):
    """
    Error indicating a fault has occured in the KRPC_Iterator

    Possible reasons for this can be:
        * There are no nodes in the routing table and no nodes
            were provided as arguments into the iterator
        * All outbound queries timed out

    The reason can be accessed as a string in the 'reason' attribute

    """
    def __init__(self, reason):
        """
        @param reason: a string describing the interation error
        """
        self.reason = reason


class KRPC_Iterator(KRPC_Responder):
    def __init__(self, node_id=None, _reactor=None):
        KRPC_Responder.__init__(self, node_id=node_id, _reactor=_reactor)

    def find_iterate(self, target_id, nodes=None, timeout=None):
        # find_iterate returns only nodes
        d = self._iterate(self.find_node, target_id, nodes)
        d.addCallback(lambda (nodes, peers): nodes)
        return d

    def get_iterate(self, target_id, nodes=None, timeout=None):
        # Get_iterate returns the full tuple (nodes, peers)
        d = self._iterate(self.get_peers, target_id, nodes)
        return d

    def _iterate(self, iterate_func, target_id, nodes=None, timeout=None):
        # Prepare the seed nodes
        if nodes is None:
            # If no nodes are supplied, we have to
            # get some from the routing table
            seed_nodes = self.routing_table.get_closest_nodes(target_id)
            if len(seed_nodes) == 0:
                return defer.fail(
                    IterationError("No nodes were supplied and no nodes "
                        + "were found in the routing table"))
        else:
            seed_nodes = nodes
        
        # Don't send duplicate queries
        seed_nodes = set(seed_nodes)

        # Send a query to each node and collect all
        # the deferred results
        deferreds = list()
        for node in seed_nodes:
            d = iterate_func(node.address, target_id, timeout)
            deferreds.append(d)

        # Create a meta-object that fires when
        # all deferred results fire
        dl = defer.DeferredList(deferreds)
        # Make sure atleast one query succeeds
        # and collect the resulting nodes/peers
        dl.addCallback(self._check_query_success_callback)
        dl.addCallback(self._collect_nodes_and_peers_callback)
        return dl

    def _check_query_success_callback(self, results):
        """
        Ensure that atleast one outbound query succeeded

        Throw an IterationError otherwise

        """
        for (success, result) in results:
            # If atleast one succeeded, we will
            # not throw an exception, so we can
            # pass the results on for further processing
            if success:
                return results
        # It is erroneous behavior for all of the
        # queries to have failed (Let the user know)
        raise IterationError("All outbound queries timed out")

    def _collect_nodes_and_peers_callback(self, results):
        """
        Extract all the nodes/peers from the query results

        @returns a tuple of iterables (new_nodes, new_peers)
        """
        new_nodes = set()
        new_peers = set()
        # result is a list of (success, result) tuples,
        # where success is a boolean, and result is
        # the callback value of the deferred
        for (was_successful, result) in results:
            if was_successful:
                # A successful response has either
                # nodes or peers for us to collect
                response = result
                if response.nodes is not None:
                    new_nodes.update(response.nodes)
                if response.peers is not None:
                    new_peers.update(response.peers)
            else:
                # A failed query provides no new
                # peers/nodes. Silently drop any such queries
                failure = result
                self._silence_error(failure)
        return (new_nodes, new_peers)

    def _silence_error(self, failure):
        """
        Trap sendQuery errors

        @see mdht.protocols.krpc_sender.sendQuery

        """
        failure.trap(TimeoutError, KRPCError)
