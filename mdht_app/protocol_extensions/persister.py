import shelve

from mdht_app import config

class NodePersister(object):
    def __init__(self, filename):
        # basically shelve all the nodes we interact with
        self._nodes = shelve.open(filename)

    def persist_node(self, node):
        self._nodes[node.node_id] = node

    def get_nodes(self):
        return list(self._nodes.values())

class NodePersistencePatcher(object):
    def __init__(self, routing_table, filename):
        self._routing_table = routing_table
        self._node_persister = NodePersister(filename)
        self._patch(self._routing_table)
        self._dict_add(self.__dict__, self._routing_table.__dict__)

    def _dict_add(self, base_dict, tail_dict):
        for key, value in tail_dict.items():
            base_dict[key] = value

    def _patch(self, routing_table):
        original = routing_table.offer_node
        def offer_node(node):
            node_accepted = original(node)
            if node_accepted:
                self.node_persister.persist_node(node)
            return node_accepted
        routing_table.offer_node = offer_node
