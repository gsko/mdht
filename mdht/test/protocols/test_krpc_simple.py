from twisted.trial import unittest
from twisted.internet import defer

from mdht.protocols.krpc_simple import LiveResult, LiveResultError, KRPC_Simple

TEST_NODE_ID = 5
TEST_PORT = 10

class LiveResult_TestCase(unittest.TestCase):
    def test_add_result_IncreasesResultSize(self):
        live_result = LiveResult()
        results = live_result.get_results()
        self.assertEquals(0, len(results))
        live_result.add_results([5])
        results = live_result.get_results()
        self.assertEquals(1, len(results))

    def test_add_results_noMoreResultsAcceptedAfterComplete(self):
        live_result = LiveResult()
        live_result.mark_completed()
        self.assertRaises(LiveResultError, live_result.add_results, [1,2])

    def _listener(self):
        self.call_count += 1

    def test_register_listener_FiresListenerOnAdd(self):
        self.call_count = 0
        live_result = LiveResult()
        live_result.register_listener(self._listener)
        live_result.add_results([1,2,3,4])
        self.assertEquals(1, self.call_count)

    def test_register_listener_FiresListenerOnCompletion(self):
        self.call_count = 0
        live_result = LiveResult()
        live_result.register_listener(self._listener)
        live_result.add_results([99,100])
        live_result.mark_completed()
        # one call for results,
        # one call for completion
        self.assertEquals(2, self.call_count)

    def test_mark_completed_SetsFlag(self):
        live_result = LiveResult()
        live_result.mark_completed()
        self.assertTrue(live_result.is_complete)

class KRPC_Simple_TestCase(unittest.TestCase):
    def setUp(self):
        self.ksimple = KRPC_Simple(TEST_NODE_ID)

    def test_get_returnsLiveResult_(self):
        live_result = self.ksimple.get(TEST_NODE_ID)

    def test_put_returnsLiveResult(self):
        live_result = self.ksimple.put(TEST_NODE_ID, TEST_PORT)
