from typing import Optional
from hybridmind.lexer import tokenize
from hybridmind.parser import Parser
from hybridmind.interpreter import execute
from hybridmind.metrics import HybridStats, print_stats

from hybridmind.fallback import rule_fallback, llm_rewrite  # you’ll paste these into fallback.py

ENABLE_LLM_FALLBACK = True
ENABLE_CONCURRENCY = True

def try_parse(text: str):
    try:
        tokens = tokenize(text)
        return Parser(tokens, enable_concurrency=ENABLE_CONCURRENCY).parse_command()
    except Exception:
        return None

def interpret(text: str, stats: Optional[HybridStats] = None):
    if stats:
        stats.total_inputs += 1
        
    # Early reject: block obviously unsafe / out-of-scope inputs before any fallback
    raw = (text or "").lower().strip()
    if any(m in raw for m in UNSAFE_MARKERS):
        if stats:
            stats.tier1_fail += 1
            stats.llm_rejected += 1  # treat as rejected-by-policy, not LLM failure
        print("[REJECTED] Unsafe / out-of-grammar input.")
        return

    # --- TIER-1: DIRECT GRAMMAR PARSE + SEMANTIC CHECK ---
    ast = try_parse(text)
    if ast is not None and is_semantically_valid(ast):
        if stats: stats.tier1_success += 1
        execute(ast)
        return

    if stats: stats.tier1_fail += 1

    # --- TIER-2: FALLBACK REWRITING (RULES + LLM) ---
    if not ENABLE_LLM_FALLBACK:
        print("[ERROR] Grammar failed and LLM fallback is disabled.")
        return

    print("[INFO] Grammar failed → fallback rewriting...")

    rb = rule_fallback(text)
    if rb:
        if stats: stats.rule_used += 1
        print(f"[RULE] Rewritten as: {rb}")
        ast_rb = try_parse(rb)
        if ast_rb is None:
            print("[ERROR] Rule fallback produced invalid command.")
            return
        execute(ast_rb)
        return

    #if no rule rewrite, try LLM    
    if stats: stats.llm_used += 1
    rewritten = llm_rewrite(text)

    if rewritten == "FAIL":
        if stats: stats.llm_fail += 1
        print("[ERROR] LLM could not produce a valid command.")
        return

    print(f"[LLM] Rewritten as: {rewritten}")

    ast2 = try_parse(rewritten)
    if ast2 is None:
        if stats: stats.llm_rejected += 1
        print("[ERROR] LLM output did not match grammar → rejected.")
        return

    if stats: stats.llm_verified_and_executed += 1
    execute(ast2)

#add stopper helper
STOPWORDS = {"me", "the", "a", "an", "please", "pls", "this", "that", "it"}
UNSAFE_MARKERS = ("import", "__", "eval", "exec", "open(", "os.", "subprocess", "def ", "class ", "```")


def is_semantically_valid(ast) -> bool:
    if ast is None:
        return False

    if ast[0] != "ACTION_CMD":
        return True

    _, action, obj, expr = ast

    # compute must have expr
    if action == "compute":
        return expr is not None

    # Reject meaningless objects like "the", "me" for show/print
    if action in ("show", "print") and obj in STOPWORDS:
        return False

    return True

def repl():
    print("HybridMind: grammar-first + rule + LLM fallback interpreter")
    print("Type 'exit' to quit.\n")
    while True:
        text = input("HybridMind>>> ").strip()
        if text.lower() == "exit":
            break
        interpret(text)
        print()

def run_small_dataset(path="data/eval_inputs.txt"):
    stats = HybridStats()
    with open(path, "r", encoding="utf-8") as f:
        inputs = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    for s in inputs:
        print(f"\n>>> {s}")
        interpret(s, stats=stats)

    print_stats(stats)

if __name__ == "__main__":
    repl()
