import unittest
from unittest.mock import patch
from hybridmind.main import interpret
from hybridmind.metrics import HybridStats

class TestEndToEndPipeline(unittest.TestCase):

    def test_1_tier1_direct(self):
        stats = HybridStats()
        interpret("compute 1 + 2 * 3", stats=stats)
        self.assertEqual(stats.tier1_success, 1)
        self.assertEqual(stats.llm_used, 0)

    def test_2_rule_fallback(self):
        stats = HybridStats()
        interpret("arrange these numbers", stats=stats)
        self.assertEqual(stats.rule_used, 1)
        self.assertEqual(stats.llm_used, 0)

    @patch("hybridmind.main.rule_fallback", return_value=None)
    @patch("hybridmind.main.llm_rewrite", return_value="sort numbers")
    def test_3_llm_rewrite_then_verify(self, _mock_llm, _mock_rule):
        stats = HybridStats()
        interpret("pls organize this list", stats=stats)
        self.assertEqual(stats.llm_used, 1)
        self.assertEqual(stats.llm_verified_and_executed, 1)

    @patch("hybridmind.main.rule_fallback", return_value=None)
    @patch("hybridmind.main.llm_rewrite", return_value="import os")
    def test_4_llm_rejected_by_grammar(self, _mock_llm, _mock_rule):
        stats = HybridStats()
        interpret("do something weird", stats=stats)
        self.assertEqual(stats.llm_used, 1)
        # Either FAIL (llm_fail) or rejected (llm_rejected) counts as handled safely
        self.assertEqual(stats.llm_rejected + stats.llm_fail, 1)
        
    @patch("hybridmind.main.rule_fallback", return_value=None)
    @patch("hybridmind.main.llm_rewrite", return_value="sort numbers while show progress")
    def test_5_end_to_end_concurrency(self, _mock_llm, _mock_rule):
        stats = HybridStats()
        interpret("please sort list and show progress at same time", stats=stats)
        self.assertEqual(stats.llm_used, 1)
        self.assertEqual(stats.llm_verified_and_executed, 1)

if __name__ == "__main__":
    unittest.main(verbosity=2)
