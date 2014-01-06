from twisted.trial import unittest

from mdht.protocols import krpc_simple

TEST_NODE_ID = 5

class KRPC_Simple_TestCase(unittest.TestCase):
    def test_constructor(self):
        _ = krpc_simple.KRPC_Simple(TEST_NODE_ID)
