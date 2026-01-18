import time
import re
import io
import contextlib
from dataclasses import dataclass
from typing import List, Dict, Optional

from hybridmind.lexer import tokenize
from hybridmind.parser import Parser
from hybridmind.interpreter import execute, env


# ---------------------------
# Rule fallback (same logic as fallback.py, but kept local so this script
# works even if transformers/torch aren’t installed)
# ---------------------------
def rule_fallback(user_text: str) -> Optional[str]:
    t = (user_text or "").lower().strip()

    # store 99 in variable score  -> set score = 99
    m = re.search(r"\b(store|put|save)\s+(\d+(?:\.\d+)?)\s+(in|into)\s+(variable|var)\s+([a-z_]\w*)\b", t)
    if m:
        value = m.group(2)
        name = m.group(5)
        return f"set {name} = {value}"

    # calculate 5 times (2 plus 3) -> compute 5 * (2 + 3)
    if t.startswith("calculate "):
        expr = t[len("calculate "):].strip()
        expr = (expr
            .replace("plus", "+")
            .replace("minus", "-")
            .replace("times", "*")
            .replace("multiplied by", "*")
            .replace("divided by", "/")
        )
        expr = re.sub(r"\s+", " ", expr)
        return f"compute {expr}"

    # show the result / display result -> print result
    if "result" in t and any(w in t for w in ["print", "show", "display"]):
        return "print result"

    # organize list while showing status -> sort numbers while show progress
    if "while" in t and ("progress" in t or "status" in t):
        if any(w in t for w in ["sort", "arrange", "organize"]):
            return "sort numbers while show progress"

    # sort/arrange/organize list/numbers -> sort numbers
    if any(w in t for w in ["sort", "arrange", "organize"]) and any(w in t for w in ["list", "numbers", "number"]):
        return "sort numbers"

    # show progress/status -> show progress
    if any(w in t for w in ["progress", "status"]) and any(w in t for w in ["show", "display", "print"]):
        return "show progress"

    return None


# ---------------------------
# Grammar utilities (same idea as main.py)
# ---------------------------
STOPWORDS = {"me", "the", "a", "an", "please", "pls", "this", "that", "it"}

def try_parse(text: str, enable_concurrency: bool = True):
    tokens = tokenize(text)
    return Parser(tokens, enable_concurrency=enable_concurrency).parse_command()

def is_semantically_valid(ast) -> bool:
    if ast is None:
        return False
    if ast[0] != "ACTION_CMD":
        return True
    _, action, obj, expr = ast
    if action == "compute":
        return expr is not None
    if action in ("show", "print") and obj in STOPWORDS:
        return False
    return True


# ---------------------------
# Evaluation setup
# ---------------------------
@dataclass
class StepResult:
    executed: bool
    correct: bool
    latency_s: float

def load_eval_inputs(path: str) -> List[str]:
    lines: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            lines.append(s)
    return lines

# For THIS eval_input.txt sequence, these are the expected env checkpoints.
# (We score “correct” if env matches what should be true at that step.)
EXPECTED_AFTER_STEP: List[Dict[str, object]] = [
    {"result": 7},                         # compute 1 + 2 * 3
    {"result": 7, "x": 10},                # set x = 10
    {"result": 7, "x": 10},                # if x > 5 then print result (no state change)
    {"result": 7, "x": 10},                # sort numbers (no state change)
    {"result": 7, "x": 10},                # sort numbers while show progress (no state change)
    {"result": 7, "x": 10},                # pls sort this list -> sort numbers
    {"result": 7, "x": 10},                # arrange these numbers -> sort numbers
    {"result": 7, "x": 10},                # organize list while showing status -> parallel
    {"result": 7, "x": 10},                # show the result -> print result
    {"result": 7, "x": 10, "score": 99},   # store 99 in variable score -> set score = 99
    {"result": 25, "x": 10, "score": 99},  # calculate 5 times (2 plus 3) -> compute ...
]

def env_matches(expected: Dict[str, object]) -> bool:
    for k, v in expected.items():
        if env.get(k) != v:
            return False
    return True


def run_grammar_only(inputs: List[str]) -> List[StepResult]:
    env.clear()
    results: List[StepResult] = []

    for i, s in enumerate(inputs):
        t0 = time.perf_counter()
        executed_ok = False
        correct = False

        try:
            ast = try_parse(s, enable_concurrency=True)
            if ast is not None and is_semantically_valid(ast):
                with contextlib.redirect_stdout(io.StringIO()):
                    execute(ast)
                executed_ok = True
        except Exception:
            executed_ok = False

        latency = time.perf_counter() - t0
        if executed_ok:
            correct = env_matches(EXPECTED_AFTER_STEP[i])

        results.append(StepResult(executed_ok, correct, latency))

    return results


def run_hybrid(inputs: List[str]) -> List[StepResult]:
    """Hybrid here = Tier-1 grammar, else rule_fallback, then grammar again."""
    env.clear()
    results: List[StepResult] = []

    for i, s in enumerate(inputs):
        t0 = time.perf_counter()
        executed_ok = False
        correct = False

        try:
            ast = None
            try:
                ast = try_parse(s, enable_concurrency=True)
            except Exception:
                ast = None

            if ast is not None and is_semantically_valid(ast):
                with contextlib.redirect_stdout(io.StringIO()):
                    execute(ast)
                executed_ok = True
            else:
                rb = rule_fallback(s)
                if rb:
                    ast2 = try_parse(rb, enable_concurrency=True)
                    with contextlib.redirect_stdout(io.StringIO()):
                        execute(ast2)
                    executed_ok = True

        except Exception:
            executed_ok = False

        latency = time.perf_counter() - t0
        if executed_ok:
            correct = env_matches(EXPECTED_AFTER_STEP[i])

        results.append(StepResult(executed_ok, correct, latency))

    return results


def summarize(mode: str, results: List[StepResult]) -> Dict[str, object]:
    n = len(results)
    executed = sum(1 for r in results if r.executed)
    correct = sum(1 for r in results if r.correct)
    total_time = sum(r.latency_s for r in results)
    avg_ms = (total_time / n) * 1000.0 if n else 0.0
    return {
        "Mode": mode,
        "Inputs": n,
        "Executed": executed,
        "Exec Rate": f"{(executed/n*100):.1f}%",
        "Correct Steps": correct,
        "Correctness Rate": f"{(correct/n*100):.1f}%",
        "Total Time (s)": f"{total_time:.3f}",
        "Avg Latency (ms)": f"{avg_ms:.1f}",
    }


def print_markdown_table(rows: List[Dict[str, object]]) -> None:
    if not rows:
        print("(no rows)")
        return

    headers = list(rows[0].keys())

    # Decide alignment per column: left for "Mode", right for numeric-ish columns
    def is_numberish(x: object) -> bool:
        s = str(x).strip()
        if s.endswith("%"):
            s = s[:-1].strip()
        try:
            float(s)
            return True
        except Exception:
            return False

    aligns = {}
    for h in headers:
        # If any row value looks numeric => right align, else left
        aligns[h] = "right" if any(is_numberish(r.get(h, "")) for r in rows) else "left"
    # Force Mode to left if present
    if "Mode" in headers:
        aligns["Mode"] = "left"

    # Compute column widths (header vs values)
    widths = {h: len(str(h)) for h in headers}
    for r in rows:
        for h in headers:
            widths[h] = max(widths[h], len(str(r.get(h, ""))))

    # Helpers to format cells
    def fmt_cell(text: object, width: int, align: str) -> str:
        s = str(text)
        return s.ljust(width) if align == "left" else s.rjust(width)

    # Markdown separator with alignment markers
    def sep_cell(width: int, align: str) -> str:
        if width < 3:
            width = 3
        if align == "left":
            return ":" + "-" * (width - 1)          # :---
        else:
            return "-" * (width - 1) + ":"          # ---:

    # Print header
    header_row = "| " + " | ".join(fmt_cell(h, widths[h], "left") for h in headers) + " |"
    sep_row    = "| " + " | ".join(sep_cell(widths[h], aligns[h]) for h in headers) + " |"
    print(header_row)
    print(sep_row)

    # Print rows
    for r in rows:
        row_str = "| " + " | ".join(
            fmt_cell(r.get(h, ""), widths[h], aligns[h]) for h in headers
        ) + " |"
        print(row_str)


if __name__ == "__main__":
    inputs = load_eval_inputs("data/eval_input.txt")

    grammar_results = run_grammar_only(inputs)
    hybrid_results = run_hybrid(inputs)

    rows = [
        summarize("Grammar-only", grammar_results),
        summarize("Hybrid", hybrid_results),
    ]

    print_markdown_table(rows)
