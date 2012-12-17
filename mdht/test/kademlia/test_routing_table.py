from twisted.trial import unittest

from mdht import constants
from mdht.contact import Node
from mdht.kademlia import routing_table
from mdht.kademlia.kbucket import KBucket
from mdht.kademlia.routing_table import _TreeNode, TreeRoutingTable, \
                                         SubsecondRoutingTable
from mdht.test import testing_data

# As long the id is unique per test case, this
# function generates non-conflicting nodes
# with proper addresses
def generate_node(id):
    addr = ("127.0.0.1", id % (2**16 - 1))
    return Node(id, addr)

def nodes_in_rt(rt):
    kbuckets = rt.get_kbuckets()
    nodes = []
    for kbucket in kbuckets:
        nodes.extend(kbucket.get_nodes())
    return nodes

def node_id_sequence(start, stop, multiplier):
    l = []
    while start < stop:
        l.append(start)
        start *= multiplier
    return l

def extract_id(node):
    return node.node_id

class TreeRoutingTableTestCase(unittest.TestCase):
    # The following tests required a k value of 8
    # so monkey patch 8 as a hardcoded value
    def setUp(self):
        self.orig_k = constants.k
        constants.k = 8

    def tearDown(self):
        constants.k = self.orig_k

    def test_offer_node_oneNode(self):
        rt = TreeRoutingTable(node_id=2**16)
        node_accepted = rt.offer_node(generate_node(15))
        self.assertTrue(node_accepted)

    def test_offer_node_remove_node_get_node_sixteenNodes(self):
        # Note: It is important to choose
        # a proper clustering of the node IDs for the
        # routing table to accept the nodes
        rt = TreeRoutingTable(node_id=1)
        # 2**160 / 2**156 == 2**4 == 16
        # Insert nodes (offer_node)
        for node_id in range(0, 2**160, 2**156):
            node_accepted = rt.offer_node(generate_node(node_id + 1))
            self.assertTrue(node_accepted)
        self.assertEquals(16, len(nodes_in_rt(rt)))
        for node in nodes_in_rt(rt):
            # Retrieve nodes (get_node)
            n = rt.get_node(node.node_id)
            self.assertEquals(node, n)
            # Remove nodes (remove_node)
            node_removed = rt.remove_node(node)
            self.assertTrue(node_removed)
        self.assertEquals(0, len(nodes_in_rt(rt)))

    def test_offer_node_properNumKBuckets(self):
        rt = TreeRoutingTable(node_id=1)
        # range(2, 9) generates 7 numbers
        for node_id in range(2, 9):
            rt.offer_node(generate_node(node_id))
        rt.offer_node(generate_node(2**158))
        rt.offer_node(generate_node(2**159))
        self.assertEquals(2, len(rt.get_kbuckets()))

    def test_get_closest_nodes_noRecursion(self):
        rt = TreeRoutingTable(node_id=1)
        target = 2**160 - 5
        for node_id in [2, 4, 8, 2**158, 2**159]:
            rt.offer_node(generate_node(node_id))
        closest_nodes = rt.get_closest_nodes(target, 2)
        self.assertEquals(map(extract_id, closest_nodes), [2**159, 2**158])

    def test_get_closest_nodes_oneLevelRecursion(self):
        rt = TreeRoutingTable(node_id=1)
        target = 2**160 - 5
        # 7 nodes close to the target
        for node_id in node_id_sequence(2**150, 2**157, 2):
            rt.offer_node(generate_node(node_id))
        # 1 node close to our node id
        rt.offer_node(generate_node(5))
        closest_nodes = rt.get_closest_nodes(target)
        expectedIDs = node_id_sequence(2**150, 2**157, 2)
        expectedIDs.append(5)
        expectedIDs.sort(key = lambda ID: ID ^ target)
        self.assertEquals(len(expectedIDs), len(closest_nodes))
        self.assertEquals(expectedIDs, map(extract_id, closest_nodes))

    def test_get_closest_nodes_multiLevelRecursion(self):
        rt = TreeRoutingTable(node_id=2**160-1)
        target = 1
        rand_list = testing_data.random_one_hundred_IDs
        dist = lambda x, y: x ^ y
        rand_list.sort(key = lambda ID: dist(ID, target))
        expectedIDs = rand_list[:constants.k]
        for ID in rand_list:
            rt.offer_node(generate_node(ID))
        closest_nodes = rt.get_closest_nodes(target)
        self.assertEquals(expectedIDs, map(extract_id, closest_nodes))

    def test_split_validNormal(self):
        k = KBucket(range_min=0, range_max=32, maxsize=2)
        tnode = _TreeNode(k)
        tnode.kbucket.offer_node(generate_node(11))
        tnode.kbucket.offer_node(generate_node(22))
        rt = TreeRoutingTable(node_id=17)
        rt.active_kbuckets.append(tnode.kbucket)
        split_correctly = rt._split(tnode)
        self.assertTrue(split_correctly)
        self.assertEquals(1, len(tnode.lchild.kbucket.get_nodes()))
        self.assertEquals(1, len(tnode.rchild.kbucket.get_nodes()))
        self.assertFalse(tnode.is_leaf())

    def test_split_invalidNotLeaf(self):
        k = KBucket(range_min=0, range_max=32, maxsize=2)
        tnode = _TreeNode(k)
        rt = TreeRoutingTable(node_id=12)
        rt.active_kbuckets.append(tnode.kbucket)
        split_correctly = rt._split(tnode)
        self.assertTrue(split_correctly)
        # Treenode has already been split (so it isnt a leaf)
        split_correctly = rt._split(tnode)
        self.assertFalse(split_correctly)

    def test_split_invalidNotSplittable(self):
        # KBucket is too small to split
        k = KBucket(range_min=0, range_max=4, maxsize=2)
        tnode = _TreeNode(k)
        rt = TreeRoutingTable(node_id=2)
        rt.active_kbuckets.append(tnode.kbucket)
        split_correctly = rt._split(tnode)
        self.assertFalse(split_correctly)

    def test_split_invalidNodeID(self):
        k = KBucket(range_min=0, range_max=16, maxsize=2)
        tnode = _TreeNode(k)
        rt = TreeRoutingTable(node_id=122)
        rt.active_kbuckets.append(tnode.kbucket)
        # 122 doesnt fit in [0, 16)
        split_correctly = rt._split(tnode)
        self.assertFalse(split_correctly)

    
class SubsecondRoutingTableTestCase(unittest.TestCase):    
    # The following tests require a hardcoded
    # value of constants.k = 8 to function
    def setUp(self):
        self.orig_k = constants.k
        constants.k = 8

    def tearDown(self):
        constants.k = self.orig_k

    # This is used as a helper function for the split
    # tests below
    def _split_and_assert_sizes(self, rt, tnode, lsize, rsize):
        split_correctly = rt._split(tnode)
        self.assertTrue(split_correctly)
        lbucket = tnode.lchild.kbucket
        rbucket = tnode.rchild.kbucket
        self.assertEquals(lsize, lbucket.maxsize)
        self.assertEquals(rsize, rbucket.maxsize)

    def test_split_validLeftOneLevel(self):
        # node_id 17 will cause the right kbucket to take on the larger size
        rt = SubsecondRoutingTable(17)
        self._split_and_assert_sizes(rt, rt.root, 8, 128)

    def test_split_validRightOneLevel(self):
        # node_id 2**159 + 1 will cause the
        # left kbucket to take on the larger size
        rt = SubsecondRoutingTable(2**159 + 1)
        self._split_and_assert_sizes(rt, rt.root, 128, 8)

    def test_split_validLeftAllTheWayDown(self):
        # node_id 1 will cause the right kbucket to take on the larger size
        rt = SubsecondRoutingTable(1)
        self._split_and_assert_sizes(rt, rt.root, 8, 128)
        lchild = rt.root.lchild
        self._split_and_assert_sizes(rt, lchild, 8, 64)
        lchild = lchild.lchild
        self._split_and_assert_sizes(rt, lchild, 8, 32)
        lchild = lchild.lchild
        self._split_and_assert_sizes(rt, lchild, 8, 16)
        lchild = lchild.lchild
        self._split_and_assert_sizes(rt, lchild, 8, 8)

    def test_offer_node_secondKBucketSplit(self):
        # ID of 2**160 - 1 will cause KBuckets on the left
        # side of the tree to expand in size (ie 128 maxsize)
        rt = SubsecondRoutingTable(2**160 - 1)
        # overflow first bucket
        for num in range(9):
            rt.offer_node(generate_node(num))
        self.assertFalse(rt.root.is_leaf())
        lchild = rt.root.lchild
        rchild = rt.root.rchild
        self.assertEquals(128, lchild.kbucket.maxsize)
        self.assertEquals(8, rchild.kbucket.maxsize)
        self.assertTrue(lchild.is_leaf())
        self.assertTrue(rchild.is_leaf())
        # overflow second bucket
        for num in range(2**159, 2**159+9):
            rt.offer_node(generate_node(num))
        rl_child = rchild.lchild
        rr_child = rchild.rchild
        self.assertEquals(64, rl_child.kbucket.maxsize)
        self.assertEquals(8, rr_child.kbucket.maxsize)

class TreeNodeTestCase(unittest.TestCase):
    def test_is_leaf(self):
        k = KBucket(range_min=0, range_max=32, maxsize=20)
        tnode = _TreeNode(k)
        self.assertTrue(tnode.is_leaf())
        # Manually attach two new _TreeNode children
        tnode.lchild = _TreeNode(k)
        tnode.rchild = _TreeNode(k)
        self.assertFalse(tnode.is_leaf())
