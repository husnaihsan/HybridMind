"""
================================================================================
HybridMind Test Suite (REAL)
WIF3010: Programming and Language Paradigm - Semester 1, 2025/2026
================================================================================
Project: HybridMind: Grammar-Driven, LLM-Assisted Language Processor
Group: Code Wizard

Total Test Cases: 35
================================================================================

"""

import time
import threading
import unittest
from unittest.mock import patch
from hybridmind.main import interpret
from hybridmind.metrics import HybridStats

# ============================================================================
# IMPORT REAL HYBRIDMIND MODULES (CONNECTED TO src/hybridmind/*)
# ============================================================================

from hybridmind.lexer import tokenize
from hybridmind.parser import Parser
import hybridmind.interpreter as interp
from hybridmind.interpreter import eval_expr, eval_condition
from hybridmind.fallback import rule_fallback, is_safe_candidate


# Helper: parse using the REAL parser (with concurrency enabled by default)
def parse_real(text: str):
    tokens = tokenize(text)
    try:
        # Prefer parser that supports enable_concurrency flag
        return Parser(tokens, enable_concurrency=True).parse_command()
    except TypeError:
        # Backward compatibility if Parser(tokens) only
        return Parser(tokens).parse_command()


# ============================================================================
# TEST CATEGORY 1: LEXICAL ANALYZER (5 tests)
# ============================================================================

class TestLexicalAnalyzer(unittest.TestCase):
    """Tests for the tokenizer - converting input to tokens"""

    def test_TC1_1_action_keywords(self):
        """TC1.1: Recognize action keywords (sort, print, show, compute)"""
        self.assertEqual(tokenize("sort")[0], ("ACTION", "sort"))
        self.assertEqual(tokenize("print")[0], ("ACTION", "print"))
        self.assertEqual(tokenize("compute")[0], ("ACTION", "compute"))

    def test_TC1_2_operators(self):
        """TC1.2: Recognize arithmetic and comparison operators"""
        self.assertEqual(tokenize("+")[0], ("PLUS", "+"))
        self.assertEqual(tokenize(">")[0], ("GT", ">"))
        self.assertEqual(tokenize(">=")[0], ("GE", ">="))
        self.assertEqual(tokenize("==")[0], ("EQ", "=="))

    def test_TC1_3_numbers(self):
        """TC1.3: Recognize integer and decimal numbers"""
        self.assertEqual(tokenize("42")[0], ("NUMBER", "42"))
        self.assertEqual(tokenize("3.14")[0], ("NUMBER", "3.14"))

    def test_TC1_4_full_command(self):
        """TC1.4: Tokenize complete command with multiple tokens"""
        result = tokenize("sort numbers while show progress")
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], ("ACTION", "sort"))
        self.assertEqual(result[2], ("WHILE", "while"))

    def test_TC1_5_invalid_character(self):
        """TC1.5: Reject invalid characters"""
        with self.assertRaises(ValueError):
            tokenize("sort @numbers")


# ============================================================================
# TEST CATEGORY 2: PARSER (6 tests)
# ============================================================================

class TestParser(unittest.TestCase):
    """Tests for the recursive descent parser - building AST"""

    def parse(self, text):
        return parse_real(text)

    def test_TC2_1_simple_action(self):
        """TC2.1: Parse simple action command"""
        ast = self.parse("sort numbers")
        self.assertEqual(ast[0], "ACTION_CMD")
        self.assertEqual(ast[1], "sort")
        self.assertEqual(ast[2], "numbers")

    def test_TC2_2_compute_expression(self):
        """TC2.2: Parse compute with arithmetic expression"""
        ast = self.parse("compute 5 + 3")
        self.assertEqual(ast[0], "ACTION_CMD")
        self.assertEqual(ast[1], "compute")
        # Expression should be present and be a BINOP
        self.assertIsNotNone(ast[3])
        self.assertEqual(ast[3][0], "BINOP")

    def test_TC2_3_assignment(self):
        """TC2.3: Parse variable assignment"""
        ast = self.parse("set x = 10")
        self.assertEqual(ast[0], "ASSIGN")
        self.assertEqual(ast[1], "x")
        self.assertEqual(ast[2], ("NUM", 10))

    def test_TC2_4_conditional(self):
        """TC2.4: Parse IF-THEN conditional"""
        ast = self.parse("if x > 10 then print result")
        self.assertEqual(ast[0], "IF")
        self.assertEqual(ast[1][0], "COND")
        self.assertEqual(ast[1][1], "GT")

    def test_TC2_5_parallel_command(self):
        """TC2.5: Parse parallel/concurrent command"""
        ast = self.parse("sort numbers while show progress")
        self.assertEqual(ast[0], "PARALLEL")
        self.assertEqual(ast[1][1], "sort")   # Left command action
        self.assertEqual(ast[2][1], "show")   # Right command action

    def test_TC2_6_syntax_error(self):
        """TC2.6: Reject malformed input"""
        # Missing THEN
        with self.assertRaises(SyntaxError):
            self.parse("if x > 5 print result")


# ============================================================================
# TEST CATEGORY 3: INTERPRETER (6 tests)
# ============================================================================

class TestInterpreter(unittest.TestCase):
    """Tests for expression and condition evaluation"""

    def setUp(self):
        # Reset REAL interpreter environment
        interp.env = {}

    def test_TC3_1_arithmetic_operations(self):
        """TC3.1: Evaluate basic arithmetic (+, -, *, /)"""
        self.assertEqual(eval_expr(("BINOP", "PLUS", ("NUM", 5), ("NUM", 3))), 8)
        self.assertEqual(eval_expr(("BINOP", "MINUS", ("NUM", 10), ("NUM", 4))), 6)
        self.assertEqual(eval_expr(("BINOP", "TIMES", ("NUM", 6), ("NUM", 7))), 42)
        self.assertEqual(eval_expr(("BINOP", "DIV", ("NUM", 20), ("NUM", 4))), 5.0)

    def test_TC3_2_operator_precedence(self):
        """TC3.2: Verify operator precedence (multiply before add)"""
        # 2 + 3 * 4 = 14
        mult = ("BINOP", "TIMES", ("NUM", 3), ("NUM", 4))
        add = ("BINOP", "PLUS", ("NUM", 2), mult)
        self.assertEqual(eval_expr(add), 14)

    def test_TC3_3_nested_expression(self):
        """TC3.3: Evaluate nested/complex expression"""
        # (2 + 3) * 4 = 20
        inner = ("BINOP", "PLUS", ("NUM", 2), ("NUM", 3))
        outer = ("BINOP", "TIMES", inner, ("NUM", 4))
        self.assertEqual(eval_expr(outer), 20)

    def test_TC3_4_variable_reference(self):
        """TC3.4: Evaluate variable from environment"""
        interp.env["score"] = 85
        self.assertEqual(eval_expr(("VAR", "score")), 85)
        self.assertEqual(eval_expr(("VAR", "undefined")), 0)  # Default

    def test_TC3_5_comparison_operators(self):
        """TC3.5: Evaluate all comparison operators"""
        self.assertTrue(eval_condition(("COND", "GT", ("NUM", 10), ("NUM", 5))))
        self.assertTrue(eval_condition(("COND", "LT", ("NUM", 3), ("NUM", 7))))
        self.assertTrue(eval_condition(("COND", "EQ", ("NUM", 42), ("NUM", 42))))
        self.assertTrue(eval_condition(("COND", "GE", ("NUM", 5), ("NUM", 5))))
        self.assertTrue(eval_condition(("COND", "LE", ("NUM", 5), ("NUM", 5))))

    def test_TC3_6_condition_with_variable(self):
        """TC3.6: Evaluate condition using variable"""
        interp.env["score"] = 85
        cond = ("COND", "GT", ("VAR", "score"), ("NUM", 60))
        self.assertTrue(eval_condition(cond))


# ============================================================================
# TEST CATEGORY 4: CONCURRENCY (4 tests)
# ============================================================================

class TestConcurrency(unittest.TestCase):
    """Tests for parallel execution (connected to REAL interpreter execution)."""

    def setUp(self):
        interp.env = {}

    def test_TC4_1_parallel_faster_than_sequential(self):
        """TC4.1: Parallel execution is faster than sequential (using patched real interpreter hooks)."""
        # Patch the real interpreter actions to be finite and time-based
        def slow_sort(_obj):
            time.sleep(0.2)

        def slow_progress(_label="progress"):
            time.sleep(0.2)

        left = ("ACTION_CMD", "sort", "numbers", None)
        right = ("ACTION_CMD", "show", "progress", None)
        par = ("PARALLEL", left, right)

        with patch.object(interp, "do_sort", side_effect=slow_sort), \
             patch.object(interp, "show_progress", side_effect=slow_progress):

            # Sequential timing (execute left then right)
            start = time.time()
            interp.execute(left)
            interp.execute(right)
            seq_time = time.time() - start

            # Parallel timing
            start = time.time()
            interp.execute(par)
            par_time = time.time() - start

        self.assertTrue(
            par_time < seq_time * 0.75,
            f"Parallel ({par_time:.2f}s) should be faster than sequential ({seq_time:.2f}s)"
        )

    def test_TC4_2_both_tasks_complete(self):
        """TC4.2: Both parallel tasks complete successfully (real interpreter, patched actions)."""
        completed = {"main": False, "side": False}

        def mark_sort(_obj):
            time.sleep(0.05)
            completed["main"] = True

        def mark_progress(_label="progress"):
            time.sleep(0.05)
            completed["side"] = True

        left = ("ACTION_CMD", "sort", "numbers", None)
        right = ("ACTION_CMD", "show", "progress", None)
        par = ("PARALLEL", left, right)

        with patch.object(interp, "do_sort", side_effect=mark_sort), \
             patch.object(interp, "show_progress", side_effect=mark_progress):
            interp.execute(par)

        self.assertTrue(completed["main"] and completed["side"])

    def test_TC4_3_stop_event_works(self):
        """TC4.3: Stop event correctly signals thread termination (using real _stop_progress)."""
        # We patch do_sort to finish quickly and show_progress to loop until stop is set.
        counter = {"value": 0}

        def fast_sort(_obj):
            time.sleep(0.15)

        def looping_progress(_label="progress"):
            # Loop until interpreter signals stop
            while not interp._stop_progress.is_set():
                counter["value"] += 1
                time.sleep(0.02)

        left = ("ACTION_CMD", "sort", "numbers", None)
        right = ("ACTION_CMD", "show", "progress", None)

        with patch.object(interp, "do_sort", side_effect=fast_sort), \
             patch.object(interp, "show_progress", side_effect=looping_progress):
            # Call run_parallel directly to verify stop behaviour
            interp.run_parallel(left, right)

        self.assertTrue(counter["value"] > 0, "Progress should have incremented at least once.")
        self.assertTrue(interp._stop_progress.is_set(), "Stop event should be set after parallel run finishes.")

    def test_TC4_4_parallel_ast_structure(self):
        """TC4.4: Parser creates correct PARALLEL AST node"""
        ast = parse_real("sort numbers while show progress")
        self.assertEqual(ast[0], "PARALLEL")
        self.assertEqual(len(ast), 3)  # (PARALLEL, left, right)


# ============================================================================
# TEST CATEGORY 5: LLM FALLBACK & AMBIGUITY (8 tests)
# ============================================================================

class TestLLMFallback(unittest.TestCase):
    """Tests for two-tier parsing and ambiguity resolution (real lexer/parser + real fallback helpers)."""

    # --- Tier 1: Grammar Success ---
    def test_TC5_1_tier1_canonical_sort(self):
        """TC5.1: Canonical command parses in Tier 1 (no LLM needed)"""
        ast = parse_real("sort numbers")
        self.assertEqual(ast[0], "ACTION_CMD")

    def test_TC5_2_tier1_canonical_parallel(self):
        """TC5.2: Canonical parallel command parses in Tier 1"""
        ast = parse_real("sort numbers while show progress")
        self.assertEqual(ast[0], "PARALLEL")

    # --- Tier 2: Grammar Fails, LLM Needed ---
    def test_TC5_3_tier2_unrecognized_verb(self):
        """TC5.3: Unrecognized verb 'organize' triggers Tier 2 (parser should fail)"""
        with self.assertRaises(SyntaxError):
            parse_real("organize these numbers")

    def test_TC5_4_tier2_informal_phrasing(self):
        """TC5.4: Informal phrasing fails grammar (needs fallback)"""
        # "pls" will tokenize as ID and parser expects ACTION at the start -> SyntaxError
        with self.assertRaises(SyntaxError):
            parse_real("pls sort this list")

    # --- Rule-Based Fallback ---
    def test_TC5_5_rule_fallback_sort(self):
        """TC5.5: Rule fallback rewrites 'arrange' to 'sort'"""
        result = rule_fallback("arrange the numbers")
        self.assertEqual(result, "sort numbers")

    def test_TC5_6_rule_fallback_parallel(self):
        """TC5.6: Rule fallback handles parallel with synonyms"""
        result = rule_fallback("organize list while showing status")
        self.assertEqual(result, "sort numbers while show progress")

    # --- Safety Validation ---
    def test_TC5_7_safety_accepts_valid(self):
        """TC5.7: Safety check accepts valid canonical commands"""
        self.assertTrue(is_safe_candidate("sort numbers"))
        self.assertTrue(is_safe_candidate("compute 5 + 3"))
        self.assertTrue(is_safe_candidate("if x > 5 then print result"))

    def test_TC5_8_safety_rejects_malicious(self):
        """TC5.8: Safety check rejects code injection attempts"""
        self.assertFalse(is_safe_candidate("import os"))
        self.assertFalse(is_safe_candidate("__name__"))
        self.assertFalse(is_safe_candidate("sort\nimport os"))
        self.assertFalse(is_safe_candidate("random text"))


# ============================================================================
# TEST CATEGORY 6: EDGE CASES & INTEGRATION (6 tests)
# ============================================================================

class TestEdgeCasesAndIntegration(unittest.TestCase):
    """Tests for boundary conditions and end-to-end workflows (real implementation)."""

    def setUp(self):
        interp.env = {}

    def test_TC6_1_zero_and_negative(self):
        """TC6.1: Handle zero and negative number operations"""
        self.assertEqual(eval_expr(("BINOP", "TIMES", ("NUM", 0), ("NUM", 100))), 0)
        self.assertEqual(eval_expr(("BINOP", "MINUS", ("NUM", 5), ("NUM", 10))), -5)

    def test_TC6_2_decimal_arithmetic(self):
        """TC6.2: Handle decimal number arithmetic"""
        result = eval_expr(("BINOP", "PLUS", ("NUM", 3.14), ("NUM", 2.86)))
        self.assertAlmostEqual(result, 6.0, places=5)

    def test_TC6_3_case_insensitive(self):
        """TC6.3: Input is case-insensitive"""
        tokens = tokenize("SORT NUMBERS")
        self.assertEqual(tokens[0], ("ACTION", "sort"))

    def test_TC6_4_boundary_comparison(self):
        """TC6.4: Boundary conditions (equal values)"""
        self.assertFalse(eval_condition(("COND", "GT", ("NUM", 5), ("NUM", 5))))
        self.assertTrue(eval_condition(("COND", "GE", ("NUM", 5), ("NUM", 5))))

    def test_TC6_5_full_workflow_compute(self):
        """TC6.5: End-to-end: interpret → grammar parse → execute → metrics updated"""
        interp.env = {}
        stats = HybridStats()

        # Silence console output during tests
        with patch("builtins.print"):
            interpret("compute 10 + 20", stats=stats)

        # result should be stored by interpreter (default behaviour in your demo)
        self.assertEqual(interp.env.get("result"), 30)

        # metrics should reflect tier-1 success
        self.assertEqual(stats.total_inputs, 1)
        self.assertEqual(stats.tier1_success, 1)
        self.assertEqual(stats.tier1_fail, 0)


    def test_TC6_6_full_workflow_conditional(self):
        """TC6.6: End-to-end: set → if-then → metrics updated"""
        interp.env = {}
        stats = HybridStats()

        with patch("builtins.print"):
            # Ensure `result` exists so `print result` outputs something meaningful
            interpret("compute 1", stats=stats)
            interpret("set score = 75", stats=stats)
            interpret("if score >= 60 then print result", stats=stats)

        self.assertEqual(interp.env.get("score"), 75)
        self.assertEqual(interp.env.get("result"), 1)

        # All 3 commands should be tier-1 successes
        self.assertEqual(stats.total_inputs, 3)
        self.assertEqual(stats.tier1_success, 3)
        self.assertEqual(stats.tier1_fail, 0)



# ============================================================================
# TEST SUMMARY (optional pretty print when run directly)
# ============================================================================

TEST_SUMMARY = """
================================================================================
                    HYBRIDMIND TEST SUITE SUMMARY (REAL)
================================================================================

Category 1: Lexical Analyzer .......................... 5 tests
    TC1.1: Action keywords recognition
    TC1.2: Operators recognition
    TC1.3: Number recognition
    TC1.4: Full command tokenization
    TC1.5: Invalid character rejection

Category 2: Parser .................................... 6 tests
    TC2.1: Simple action parsing
    TC2.2: Compute expression parsing
    TC2.3: Assignment parsing
    TC2.4: Conditional parsing
    TC2.5: Parallel command parsing
    TC2.6: Syntax error handling

Category 3: Interpreter ............................... 6 tests
    TC3.1: Arithmetic operations
    TC3.2: Operator precedence
    TC3.3: Nested expressions
    TC3.4: Variable references
    TC3.5: Comparison operators
    TC3.6: Conditions with variables

Category 4: Concurrency ............................... 4 tests
    TC4.1: Parallel faster than sequential
    TC4.2: Both tasks complete
    TC4.3: Stop event signaling
    TC4.4: PARALLEL AST structure

Category 5: LLM Fallback & Ambiguity .................. 8 tests
    TC5.1: Tier 1 - canonical sort
    TC5.2: Tier 1 - canonical parallel
    TC5.3: Tier 2 - unrecognized verb
    TC5.4: Tier 2 - informal phrasing
    TC5.5: Rule fallback - sort synonym
    TC5.6: Rule fallback - parallel synonym
    TC5.7: Safety accepts valid commands
    TC5.8: Safety rejects malicious input

Category 6: Edge Cases & Integration .................. 6 tests
    TC6.1: Zero and negative numbers
    TC6.2: Decimal arithmetic
    TC6.3: Case insensitivity
    TC6.4: Boundary comparisons
    TC6.5: Full workflow - compute
    TC6.6: Full workflow - conditional

================================================================================
                         TOTAL: 35 Test Cases
================================================================================
"""


if __name__ == "__main__":
    print(TEST_SUMMARY)
    unittest.main(verbosity=2)
