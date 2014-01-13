from mdht.protocols.krpc_iterator import KRPC_Iterator

class LiveResultError(Exception):
    def __init__(self):
        pass

class LiveResult(object):
    def __init__(self):
        self.results = []
        self.listeners = set()
        self.is_complete = False

    def add_results(self, results):
        """Add an iterable of results to the LiveResult"""
        if self.is_complete:
            raise LiveResultError()
        self.results += list(results)
        self._alert_listeners()

    def get_results(self):
        """Return all results in an iterable"""
        return self.results

    def register_listener(self, listener):
        """
        Register an argument-less callable object that is fired
        whenever new results are added, or if the LiveResult has been
        marked completed and no more results will be inserted
        """
        self.listeners.add(listener)

    def mark_completed(self):
        """
        After this LiveResult is marked complete, it will fire one last
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

    def get(self, target_id):
        """
        Return a LiveResult of (node, peers) pairs
        for the torrent with an infohash of `target_id`

        (node, peers) is the contact.Node that returned the corresponding peers
        """
        live_result = LiveResult()
        search_nodes = set(self.routing_table.get_closest_nodes(target_id))

    def _get_peers_response_handler(self, response, live_result):
        if responses.peers is not None:
            pass
        if response.nodes is not None:
            pass

    def put(self, target_id, port):
        """
        Register this IP along with the given port
        for the torrent with an infohash of `target_id`
        """
        live_result = LiveResult()
