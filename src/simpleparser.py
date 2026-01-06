import re
import time
import threading

import torch
from transformers import pipeline
from dataclasses import dataclass

# for LLM dependency ratio measurement (counters + small dataset run)
@dataclass
class HybridStats:
    total_inputs: int = 0

    tier1_success: int = 0
    tier1_fail: int = 0

    rule_used: int = 0

    llm_used: int = 0
    llm_fail: int = 0
    llm_rejected: int = 0
    llm_verified_and_executed: int = 0

# ------------------------
# CONFIG
# ------------------------
ENABLE_LLM_FALLBACK = True
ENABLE_CONCURRENCY = True

# Recommended for CPU: base/small
LLM_MODEL_NAME = "google/flan-t5-large"

# ------------------------
# 1) LEXICAL ANALYZER (regex)
# ------------------------

TOKEN_SPEC = [
    ("IF",      r"if"),
    ("THEN",    r"then"),
    ("SET",     r"set"),
    ("WHILE",   r"while"),

    # STRICT grammar: only canonical actions
    ("ACTION",  r"(sort|print|show|compute)"),
    ("OBJECT",  r"(numbers|number|list|progress|result)"),

    ("GE",      r">="),
    ("LE",      r"<="),
    ("EQ",      r"=="),
    ("GT",      r">"),
    ("LT",      r"<"),

    ("ASSIGN",  r"="),
    ("PLUS",    r"\+"),
    ("MINUS",   r"-"),
    ("TIMES",   r"\*"),
    ("DIV",     r"/"),
    ("LPAREN",  r"\("),
    ("RPAREN",  r"\)"),

    ("NUMBER",  r"\d+(\.\d+)?"),
    ("ID",      r"[A-Za-z_][A-Za-z_0-9]*"),
    ("WS",      r"\s+"),
]

def tokenize(text: str):
    tokens = []
    i = 0
    text = text.strip().lower()

    while i < len(text):
        match = None
        for tok_type, tok_re in TOKEN_SPEC:
            regex = re.compile(tok_re)
            match = regex.match(text, i)
            if match:
                if tok_type != "WS":
                    tokens.append((tok_type, match.group()))
                i = match.end()
                break

        if not match:
            raise ValueError(f"Unexpected character: {text[i]}")

    return tokens

# ------------------------
# 2) PARSER (recursive-descent)
# ------------------------

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, tok_type):
        tok = self.peek()
        if tok and tok[0] == tok_type:
            self.pos += 1
            return tok
        raise SyntaxError(f"Expected {tok_type}, got {tok}")

    def parse_command(self):
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Empty command")

        if tok[0] == "IF":
            return self.parse_if()
        if tok[0] == "SET":
            return self.parse_assign()

        # Concurrency: <action_cmd> while <action_cmd>
        if ENABLE_CONCURRENCY:
            remaining = [t[0] for t in self.tokens[self.pos:]]
            if "WHILE" in remaining:
                return self.parse_parallel()

        return self.parse_action_cmd()

    def parse_parallel(self):
        left = self.parse_action_cmd()
        self.consume("WHILE")
        right = self.parse_action_cmd()
        return ("PARALLEL", left, right)

    def parse_action_cmd(self):
        action = self.consume("ACTION")[1]
        obj = None

        if self.peek() and self.peek()[0] in ("OBJECT", "ID"):
            obj = self.consume(self.peek()[0])[1]

        expr = None
        if action == "compute":
            expr = self.parse_expression()

        return ("ACTION_CMD", action, obj, expr)

    def parse_assign(self):
        self.consume("SET")
        name = self.consume("ID")[1]
        self.consume("ASSIGN")
        expr = self.parse_expression()
        return ("ASSIGN", name, expr)

    def parse_if(self):
        self.consume("IF")
        cond = self.parse_condition()
        self.consume("THEN")
        body = self.parse_command()
        return ("IF", cond, body)

    def parse_condition(self):
        left = self.parse_expression()
        tok = self.peek()
        if tok is None or tok[0] not in ("GT", "LT", "GE", "LE", "EQ"):
            raise SyntaxError("Expected comparison operator")
        op = self.consume(tok[0])[0]
        right = self.parse_expression()
        return ("COND", op, left, right)

    def parse_expression(self):
        node = self.parse_term()
        while self.peek() and self.peek()[0] in ("PLUS", "MINUS"):
            op = self.consume(self.peek()[0])[0]
            right = self.parse_term()
            node = ("BINOP", op, node, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek() and self.peek()[0] in ("TIMES", "DIV"):
            op = self.consume(self.peek()[0])[0]
            right = self.parse_factor()
            node = ("BINOP", op, node, right)
        return node

    def parse_factor(self):
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input")

        if tok[0] == "NUMBER":
            self.consume("NUMBER")
            val = float(tok[1]) if "." in tok[1] else int(tok[1])
            return ("NUM", val)

        if tok[0] == "ID":
            return ("VAR", self.consume("ID")[1])

        if tok[0] == "LPAREN":
            self.consume("LPAREN")
            expr = self.parse_expression()
            self.consume("RPAREN")
            return expr

        raise SyntaxError(f"Unexpected token in factor: {tok}")

# ------------------------
# 3) INTERPRETER
# ------------------------

env = {}
_stop_progress = threading.Event()

def eval_expr(node):
    kind = node[0]
    if kind == "NUM":
        return node[1]
    if kind == "VAR":
        return env.get(node[1], 0)
    if kind == "BINOP":
        op, left, right = node[1], node[2], node[3]
        lval = eval_expr(left)
        rval = eval_expr(right)
        if op == "PLUS":  return lval + rval
        if op == "MINUS": return lval - rval
        if op == "TIMES": return lval * rval
        if op == "DIV":   return lval / rval
    raise RuntimeError(f"Unknown expr node: {node}")

def eval_condition(node):
    _, op, left, right = node
    lval = eval_expr(left)
    rval = eval_expr(right)
    if op == "GT": return lval > rval
    if op == "LT": return lval < rval
    if op == "GE": return lval >= rval
    if op == "LE": return lval <= rval
    if op == "EQ": return lval == rval
    raise RuntimeError(f"Unknown condition op: {op}")

def do_sort(obj):
    target = obj or "numbers"
    print(f"[SORT] Sorting {target}...")
    time.sleep(2)  # simulate work
    print(f"[SORT] Done sorting {target}.")

def do_compute(expr_node):
    val = eval_expr(expr_node)
    env["result"] = val
    print(f"[COMPUTE] result = {val}")

def do_print(value):
    print(f"[PRINT] {value}")

def show_progress(label="progress"):
    i = 0
    while not _stop_progress.is_set():
        i += 1
        print(f"[PROGRESS] {label}... {i}")
        time.sleep(0.5)

def run_parallel(cmd1, cmd2):
    _stop_progress.clear()

    t1 = threading.Thread(target=lambda: execute(cmd1))
    t2 = threading.Thread(target=lambda: execute(cmd2))

    start = time.time()
    t1.start()
    t2.start()

    t1.join()
    _stop_progress.set()
    t2.join()

    elapsed = time.time() - start
    print(f"[CONCURRENCY] Done in ~{elapsed:.2f}s")

def execute(node):
    kind = node[0]

    if kind == "ASSIGN":
        _, name, expr = node
        env[name] = eval_expr(expr)
        print(f"[ASSIGN] {name} = {env[name]}")
        return

    if kind == "IF":
        _, cond, body = node
        if eval_condition(cond):
            print("[IF] condition true → executing body")
            execute(body)
        else:
            print("[IF] condition false → skipping body")
        return

    if kind == "PARALLEL":
        _, left, right = node
        print("[CONCURRENCY] Running in parallel...")
        run_parallel(left, right)
        return

    if kind == "ACTION_CMD":
        _, action, obj, expr = node

        if action == "sort":
            do_sort(obj)
            return

        if action == "compute":
            do_compute(expr)
            return

        if action in ("print", "show"):
            if obj == "result":
                do_print(env.get("result", None))
            elif obj == "progress":
                show_progress("progress")
            elif obj in env:
                do_print(env[obj])
            else:
                do_print(obj)
            return

    raise RuntimeError(f"Unknown AST node: {node}")

# ------------------------
# 4) LLM FALLBACK (Flan-T5) + SAFETY
# ------------------------

translator = None
CANON_PREFIXES = ("sort", "print", "show", "compute", "set", "if")

def load_llm():
    global translator
    if translator is not None:
        return
    print("[LLM] Loading local model...")
    device = 0 if torch.cuda.is_available() else -1
    translator = pipeline("text2text-generation", model=LLM_MODEL_NAME, device=device)
    print("[LLM] Ready.")

def is_safe_candidate(cmd: str) -> bool:
    cmd = cmd.strip().lower()
    if not cmd:
        return False

    bad_placeholders = ["expr", "op", "command"]
    if any(b in cmd for b in bad_placeholders):
        return False

    bad_markers = ["__name__", "import", "def ", "class ", "print(", "```", "{", "}", "[", "]"]
    if any(b in cmd for b in bad_markers):
        return False

    if "\n" in cmd or "\r" in cmd:
        return False

    if not cmd.startswith(CANON_PREFIXES):
        return False

    return True

def rule_fallback(user_text: str) -> str | None:
    t = user_text.lower()

    # Most important demo: sort + progress
    if "while" in t and ("progress" in t or "status" in t):
        if any(w in t for w in ["sort", "arrange", "organize"]):
            return "sort numbers while show progress"

    # single sort
    if any(w in t for w in ["sort", "arrange", "organize"]) and any(w in t for w in ["list", "numbers", "number"]):
        return "sort numbers"

    # print/show result
    if any(w in t for w in ["print", "show", "display"]) and "result" in t:
        return "print result"

    return None

def llm_rewrite(user_text: str) -> str:
    load_llm()

    prompt = f"""Task:
    - Convert the input into ONE simple straightforward command ONLY.
    - fix any ambiguities or typos, if any
    - Output MUST be a valid command following the grammar examples.

    1) compute <expr>
    2) set <id> = <expr>
    3) if <expr> <op> <expr> then <command>
    4) sort numbers
    5) print result
    6) show progress
    7) sort numbers while show progress

    Rules:
    - Output ONE line only
    - Output ONLY the command (no explanation)
    - No explanation, no bullet points, no markdown
    - If you cannot convert, output: FAIL
    - If the input is related to parallel task, output = <expr> while <expr>, eg: 'sort these numbers and show the progress at the same time' -> 'sort numbers while show progress'

    Examples:
    Input: add 5 and 10
    Output: compute 5 + 10

    Input: put 99 into variable score
    Output: set score = 99

    Input: check if score is big then show it
    Output: if score > 50 then print score

    Input: sort this list while showing progress
    Output: sort numbers while show progress


    Input: {user_text}
    Output:"""

    out = translator(
        prompt,
        max_new_tokens=32,
        do_sample=False,
        num_beams=1
    )[0]["generated_text"].strip().lower()

    out = out.splitlines()[0].strip()
    out = out.replace(":", "").replace(";", "").replace(",","").replace("(", "").replace(")", "")

    if out == "fail" or not is_safe_candidate(out):
        rb = rule_fallback(user_text)
        if rb:
            return rb
        return "FAIL"

    return out

def try_parse(text: str):
    try:
        tokens = tokenize(text)
        return Parser(tokens).parse_command()
    except Exception:
        return None

def interpret(text: str, stats: "HybridStats | None" = None):
    if stats:
        stats.total_inputs += 1

    # Tier 1: grammar-first
    ast = try_parse(text)
    if ast is not None:
        if stats:
            stats.tier1_success += 1
        execute(ast)
        return

    if stats:
        stats.tier1_fail += 1

    if not ENABLE_LLM_FALLBACK:
        print("[ERROR] Grammar failed and LLM fallback is disabled.")
        return

    # Tier 2: rule fallback first
    print("[INFO] Grammar failed → LLM fallback rewriting...")
    rb = rule_fallback(text)
    if rb:
        if stats:
            stats.rule_used += 1
        print(f"[RULE] Rewritten as: {rb}")
        ast_rb = try_parse(rb)
        # safety check (optional)
        if ast_rb is None:
            print("[ERROR] Rule fallback produced invalid command (unexpected).")
            return
        execute(ast_rb)
        return

    # Tier 2: LLM rewrite
    if stats:
        stats.llm_used += 1

    rewritten = llm_rewrite(text)
    if rewritten == "FAIL":
        if stats:
            stats.llm_fail += 1
        print("[ERROR] LLM could not produce a valid command.")
        return

    print(f"[LLM] Rewritten as: {rewritten}")

    # Grammar verification again
    ast2 = try_parse(rewritten)
    if ast2 is None:
        if stats:
            stats.llm_rejected += 1
        print("[ERROR] LLM output did not match grammar → rejected.")
        return

    if stats:
        stats.llm_verified_and_executed += 1
    execute(ast2)


# ------------------------
# 5) REPL
# ------------------------

if __name__ == "__main__":
    print("HybridMind: grammar-first + LLM fallback + concurrency")
    print("Type 'exit' to quit.\n")

    while True:
        text = input("Hybrid>>> ").strip()
        if text.lower() == "exit":
            break
        interpret(text)
        print("\n")
