from twisted.trial import unittest
from twisted.internet import defer

from mdht.protocols import krpc_simple

TEST_NODE_ID = 5
TEST_PORT = 10

class KRPC_Simple_TestCase(unittest.TestCase):
    def setUp(self):
        self.ksimple = krpc_simple.KRPC_Simple(TEST_NODE_ID)

    def test_get_returnsDeferred(self):
        d = self.ksimple.get(TEST_NODE_ID)
        self.assertTrue(isinstance(d, defer.Deferred))

    def test_put_returnsDeferred(self):
        d = self.ksimple.put(TEST_NODE_ID, TEST_PORT)
        self.assertTrue(isinstance(d, defer.Deferred))
