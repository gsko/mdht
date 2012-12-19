from twisted.trial import unittest
from twisted.python.monkey import MonkeyPatcher

from mdht import contact
from mdht import constants
from mdht.coding import basic_coder
from mdht.test.utils import Clock

monkey_patcher = MonkeyPatcher()

class NodeTestCase(unittest.TestCase):

    def setUp(self):
        # Reach into the contact module and replace
        # its time function with a custom one
        self.clock = Clock()
        monkey_patcher.addPatch(contact, "time", self.clock)
        monkey_patcher.patch()

    def tearDown(self):
        # Restore the old time module
        monkey_patcher.restore()

    def test_distance(self):
        node_ids1 = [0, 1024, 2**150, 2**159 + 124, 2**34 - 58]
        node_ids2 = [0, 857081, 6**7, 8**9 + 7**3, 4**8 + 9**10 + 18]
        for id1 in node_ids1:
            for id2 in node_ids2:
                n = contact.Node(id1, ("127.0.0.1", 8000))
                self.assertEqual(id1 ^ id2, n.distance(id2))
                n = contact.Node(id2, ("127.0.0.1", 8000))
                self.assertEqual(id2 ^ id1, n.distance(id1))

    def test_fresh(self):
        n = contact.Node(2**17, ("127.0.0.1", 8012))
        self.assertTrue(n.fresh())
        # Simulate that `constants.node_timeout' time has passed
        self.clock.set(constants.node_timeout + 1)
        self.assertFalse(n.fresh())
        # Refresh the node with a new query
        n.successful_query(10)
        self.assertTrue(n.fresh())

    def test_better_than_bothOldWithNoQueries(self):
        self.clock.set(0)
        n1 = contact.Node(2**1, ("127.0.0.1", 1111))
        n2 = contact.Node(2**2, ("127.0.0.1", 2222))
        self.clock.set(constants.node_timeout + 1)
        self.assertFalse(n1.better_than(n2))
        self.assertFalse(n2.better_than(n1))


    def test_better_than_oneFreshOneOld(self):
        self.clock.set(0)
        n_old = contact.Node(2**1, ("127.0.0.1", 1111))
        n_fresh = contact.Node(2**2, ("127.0.0.1", 2222))
        self.clock.set(constants.node_timeout + 1)
        n_fresh.successful_query(10)
        self.assertTrue(n_fresh.better_than(n_old))

    def test_better_than_oneBetterRTT(self):
        self.clock.set(0)
        n_slow = contact.Node(2**1, ("127.0.0.1", 1111))
        n_fast = contact.Node(2**2, ("127.0.0.1", 2222))
        self.clock.set(10)
        n_slow.successful_query(0)
        n_fast.successful_query(5)
        self.assertTrue(n_fast.better_than(n_slow))

class NodeCodingTestCase(unittest.TestCase):
    def setUp(self):
        encode = basic_coder.encode_address
        decode = basic_coder.decode_address
        self.encode_and_decode = lambda address: decode(encode(address))

    def test_address_str(self):
        address = ("127.0.0.1", 80)
        expected_str = "ip=127.0.0.1 port=80"
        self.assertEquals(expected_str, contact.address_str(address))
