import shelve

from mdht_app import config

# TODO

class NodePersister(object):
    def __init__(self, krpc_iterator):
        # basically shelve all the nodes we interact with
        self._nodes = shelve.open(config.PEERS_FILENAME)

    def persist_node(self, node):
        self._nodes[node.node_id] = node

    def get_nodes(self):
        return list(self._nodes.values())
