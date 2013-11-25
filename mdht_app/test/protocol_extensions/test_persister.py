from twisted.trial import unittest

from mdht.kademlia.routing_table import TreeRoutingTable
from mdht.contact import Node
from mdht_app.protocol_extensions.persister import NodePersistencePatcher

class NodePersistencePatcherTest(unittest.TestCase):
    def setUp(self):
        self.test_node_id = 5
        self.old_rt = TreeRoutingTable(self.test_node_id)
        self.new_rt = NodePersistencePatcher(
            self.old_rt, '/tmp/cae90jt319')

    def test_patchingMakesNewFunc(self):
        self.assertNotEquals(
            self.new_rt.offer_node, self.old_rt.offer_node)

    def test_patchingPersistsNodes(self):
        n = Node(5, ("127.0.0.1", 55))
        self.new_rt.offer_node(n)
        nodes = self.new_rt._node_persister.get_nodes()
        self.assertTrue(n in nodes)
