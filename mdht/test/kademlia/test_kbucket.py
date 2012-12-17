import time

from twisted.trial import unittest

from mdht import constants
from mdht.contact import Node
from mdht.kademlia import kbucket
KBucket = kbucket.KBucket

class KBucketTestCase(unittest.TestCase):
    def test_offer_node_singleNode(self):
        k = KBucket(range_min=0, range_max=60, maxsize=1)
        n = Node(25, ("127.0.0.1", 50))
        accepted_node = k.offer_node(n)
        self.assertTrue(accepted_node)

    def test_offer_node_overflowAllFresh(self):
        k = KBucket(range_min=0, range_max=60, maxsize=1)
        n1 = Node(11, ("127.0.0.1", 11))
        n2 = Node(22, ("127.0.0.1", 22))
        n3 = Node(33, ("127.0.0.1", 33))
        n4 = Node(44, ("127.0.0.1", 44))
        # Accept only first node and none others
        accepted_node = k.offer_node(n1)
        self.assertTrue(accepted_node)
        self.assertEquals(1, len(k.get_nodes()))

        accepted_node = k.offer_node(n2)
        self.assertFalse(accepted_node)
        self.assertEquals(1, len(k.get_nodes()))

        accepted_node = k.offer_node(n3)
        self.assertFalse(accepted_node)
        self.assertEquals(1, len(k.get_nodes()))

        accepted_node = k.offer_node(n4)
        self.assertFalse(accepted_node)
        self.assertEquals(1, len(k.get_nodes()))

    def test_offer_node_staleReplacement(self):
        k = KBucket(range_min=0, range_max=60, maxsize=1)
        nfresh = Node(11, ("127.0.0.1", 11))
        nstale = Node(22, ("127.0.0.1", 22))
        nstale.last_updated -= constants.node_timeout + 2
        # Insert stale
        accepted_node = k.offer_node(nstale)
        self.assertTrue(accepted_node)
        self.assertEquals(1, len(k.get_nodes()))

        # Replace with fresh
        accepted_node = k.offer_node(nfresh)
        self.assertTrue(accepted_node)
        self.assertEquals(1, len(k.get_nodes()))

        # Try (and fail to) replace with the stale
        accepted_node = k.offer_node(nstale)
        self.assertFalse(accepted_node)
        self.assertEquals(1, len(k.get_nodes()))

    def test_offer_node_invalidRange(self):
        k = KBucket(range_min=0, range_max=5, maxsize=1)
        n_invalid = Node(11, ("127.0.0.1", 11))
        self.assertRaises(kbucket.KBucketError, k.offer_node, n_invalid)

    def test_remove_node(self):
        k = KBucket(range_min=0, range_max=5, maxsize=1)
        n = Node(1, ("127.0.0.1", 1))
        k.offer_node(n)
        node_removed = k.remove_node(n)
        self.assertTrue(node_removed)
        self.assertEquals(0, len(k.get_nodes()))
        node_removed = k.remove_node(n)
        self.assertFalse(node_removed)

    def test_splittable(self):
        k = KBucket(range_min=0, range_max=2**160, maxsize=1)
        self.assertTrue(k.splittable())
        k = KBucket(range_min=0, range_max=8, maxsize=1)
        self.assertTrue(k.splittable())
        k = KBucket(range_min=0, range_max=4, maxsize=1)
        self.assertFalse(k.splittable())
        k = KBucket(range_min=0, range_max=2, maxsize=1)
        self.assertFalse(k.splittable())

    def test_split_normal(self):
        k = KBucket(range_min=0, range_max=8, maxsize=10)
        for node_num in range(8):
            n = Node(node_num, ("127.0.0.1", node_num + 1))
            k.offer_node(n)
        (kleft, kright) = k.split()
        self.assertEquals(4, len(kleft.get_nodes()))
        self.assertEquals(4, len(kright.get_nodes()))
        self.assertTrue(k.empty())

    def test_split_normalWideRange(self):
        k = KBucket(range_min=0, range_max=2**160, maxsize=8)
        for node_num in range(4):
            n = Node(node_num, ("127.0.0.1", node_num + 1))
            k.offer_node(n)
        for node_num in range(2**159, 2**159 + 4):
            n = Node(node_num, ("127.0.0.1", 55))
            k.offer_node(n)
        (kleft, kright) = k.split()
        self.assertEquals(4, len(kleft.get_nodes()))
        self.assertEquals(4, len(kright.get_nodes()))
        self.assertTrue(k.empty())

    def test_split_testRange(self):
        k = KBucket(range_min=0, range_max=32, maxsize=1)
        (l, r) = k.split()
        self.assertEquals(0, l.range_min)
        self.assertEquals(16, l.range_max)
        self.assertEquals(16, r.range_min)
        self.assertEquals(32, r.range_max)

    def test_split_tooSmall(self):
        k = KBucket(range_min=0, range_max=4, maxsize=10)
        self.assertRaises(kbucket.KBucketError, k.split)

    def test_full(self):
        k = KBucket(range_min=0, range_max=2**160, maxsize=10)
        # Make 16 nodes and insert them into a size 10 KBucket
        # 2**160 in 2**154 increments is 2**160/2**156 == 2**4 == 16
        for node_id in range(0, 2**160, 2**156):
            n = Node(node_id, ("127.0.0.1", 55))
            k.offer_node(n)
        self.assertTrue(k.full())

    def test_get_stalest_node(self):
        k = KBucket(range_min=0, range_max=2**160, maxsize=10)
        n1 = Node(11, ("127.0.0.1", 11))
        n2 = Node(21, ("127.0.0.1", 21))
        n3 = Node(31, ("127.0.0.1", 31))
        n2.last_updated -= 10
        k.offer_node(n1)
        k.offer_node(n2)
        k.offer_node(n3)
        self.assertEquals(n2, k.get_stalest_node())
