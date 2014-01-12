from mdht.protocols.krpc_iterator import KRPC_Iterator

class LiveResult(object):
    def __init__(self):
        self.results = []
        self.listeners = set()

    def add_results(self, results):
        self.results += list(results)
        for listener in self.listeners:
            listener()

    def get_results(self):
        return self.results

    def register_listener(self, listener):
        self.listeners.add(listener)


class KRPC_Simple(KRPC_Iterator):
    def __init__(self, node_id=None):
        #KRPC_Iterator.__init__(self, node_id)
        pass

    def get(self, target_id):
        pass

    def put(self, target_id, port):
        pass
