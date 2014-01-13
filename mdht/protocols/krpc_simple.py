from mdht.protocols.krpc_iterator import KRPC_Iterator
from mdht.protocols.errors import TimeoutError, KRPCError 

class LiveSearchError(Exception):
    def __init__(self):
        pass

class LiveSearch(object):
    def __init__(self, target_id):
        self.results = []
        self.listeners = set()
        # TODO refactor is_complete into is_completed()
        self.is_complete = False
        self.outstanding_queries = 0
        self.target_id = target_id
        self.queried_nodes = set()

    def add_results(self, results):
        """Add an iterable of results to the LiveSearch"""
        if self.is_complete:
            raise LiveSearchError()
        self.results += list(results)
        self._alert_listeners()

    def get_results(self):
        """Return all results in an iterable"""
        return self.results

    def register_listener(self, listener):
        """
        Register an argument-less callable object that is fired
        whenever new results are added, or if the LiveSearch has been
        marked completed and no more results will be inserted
        """
        self.listeners.add(listener)

    def mark_completed(self):
        """
        After this LiveSearch is marked complete, it will fire one last
        time and no longer accept new results
        """
        self.is_complete = True
        self._alert_listeners()

    def _alert_listeners(self):
        for listener in self.listeners:
            listener()

class KRPC_Simple(KRPC_Iterator):
    def __init__(self, node_id=None):
        KRPC_Iterator.__init__(self, node_id)
        # TODO KRPCSimple should bootstrap itself
        # -- this will require reworking of many of the krpc_simple tests
        # TODO token gathering

    def get(self, target_id):
        """
        Return a LiveSearch of (node, peers) pairs
        for the torrent with an infohash of `target_id`

        (node, peers) is the contact.Node that returned the corresponding peers
        """
        live_search = LiveSearch(target_id)
        search_nodes = set(self.routing_table.get_closest_nodes(target_id))
        if len(search_nodes) == 0:
            live_search.mark_completed()
        else:
            self._get_iterate(search_nodes, live_search)
        return live_search

    def put(self, target_id, port):
        """
        Register this IP along with the given port
        for the torrent with an infohash of `target_id`
        """
        pass

    def _get_iterate(self, nodes, live_search):
        search_nodes = nodes or []
        for node in search_nodes:
            if node in live_search.queried_nodes:
                continue
            d = self.get_peers(node.address, live_search.target_id)
            live_search.queried_nodes.add(node)
            # TODO refactor outstanding_queries and is_completed()
            # into something else. maybe add some kind of 'query()' and
            # 'ack_query()'?
            live_search.outstanding_queries += 1
            d.addCallback(self._get_peers_response_handler, live_search)
            d.addErrback(self._get_peers_error_handler, live_search)
            d.addBoth(self._check_completion, live_search)

    def _check_completion(self, _ignore, live_search):
        live_search.outstanding_queries -= 1
        if live_search.outstanding_queries == 0:
            live_search.mark_completed()

    def _get_peers_response_handler(self, response, live_search):
        if response.peers is not None:
            # TODO accumuluate peers (??)
            live_search.add_results(response.peers)
        self._get_iterate(response.nodes, live_search)

    def _get_peers_error_handler(self, failure, live_search):
        f = failure.trap(TimeoutError, KRPCError)
        # do nothing: we don't care about timeouts or errors
