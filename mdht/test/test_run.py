from twisted.trial import unittest
from twisted.python.monkey import MonkeyPatcher

from mdht import run
from mdht.run import MDHT
from mdht.test.utils import HollowReactor

monkey_patcher = MonkeyPatcher()

class MDHT_TestCase(unittest.TestCase):
    def setUp(self):
        monkey_patcher.addPatch(run, "reactor", HollowReactor())
        monkey_patcher.patch()

    def tearDown(self):
        monkey_patcher.restore()

    def test_contains_valid_funcs(self):
        """
        Test to make sure that the specified functionality has been patched in
        """
        m = MDHT(5)
        required_funcs = {"ping", "find_node",
            "get_peers", "announce_peer", "find_iterate", "get_iterate"}
        actual_funcs = set(dir(m))
        self.assertTrue(required_funcs.issubset(actual_funcs))
