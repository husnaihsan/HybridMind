import re

# ------------------------
# 1. LEXICAL ANALYZER (regex-based scanner)
# ------------------------

TOKEN_SPEC = [
    ("IF",      r"if"),
    ("THEN",    r"then"),
    ("SET",     r"set"),
    ("ACTION",  r"(sort|arrange|organize|print|show|display|compute|calculate|find|plot|load|read|save|write|sum|total)"),
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
# 2. PARSER (recursive-descent)
# ------------------------

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # utility

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, tok_type):
        tok = self.peek()
        if tok and tok[0] == tok_type:
            self.pos += 1
            return tok
        raise SyntaxError(f"Expected {tok_type}, got {tok}")

    # entry

    def parse_command(self):
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Empty command")

        if tok[0] == "IF":
            return self.parse_if()
        if tok[0] == "SET":
            return self.parse_assign()

        # default: action command
        return self.parse_action_cmd()

    # commands

    def parse_action_cmd(self):
        # e.g. "print result" or "compute 1 + 2 * 3"
        action_tok = self.consume("ACTION")
        action = action_tok[1]

        obj = None
        # optional OBJECT (e.g. "print result")
        if self.peek() and self.peek()[0] == "OBJECT":
            obj = self.consume("OBJECT")[1]

        expr = None
        # "compute" is followed by an expression
        if action == "compute":
            expr = self.parse_expression()

        return ("ACTION_CMD", action, obj, expr)

    def parse_assign(self):
        # set x = 10 + 2
        self.consume("SET")
        name = self.consume("ID")[1]
        self.consume("ASSIGN")
        expr = self.parse_expression()
        return ("ASSIGN", name, expr)

    def parse_if(self):
        # if x > 5 then print result
        self.consume("IF")
        cond = self.parse_condition()
        self.consume("THEN")
        body = self.parse_command()
        return ("IF", cond, body)

    # expressions & conditions

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
        while True:
            tok = self.peek()
            if tok and tok[0] in ("PLUS", "MINUS"):
                op = self.consume(tok[0])[0]
                right = self.parse_term()
                node = ("BINOP", op, node, right)
            else:
                break
        return node

    def parse_term(self):
        node = self.parse_factor()
        while True:
            tok = self.peek()
            if tok and tok[0] in ("TIMES", "DIV"):
                op = self.consume(tok[0])[0]
                right = self.parse_factor()
                node = ("BINOP", op, node, right)
            else:
                break
        return node

    def parse_factor(self):
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input in factor")

        if tok[0] == "NUMBER":
            self.consume("NUMBER")
            val = float(tok[1]) if "." in tok[1] else int(tok[1])
            return ("NUM", val)

        if tok[0] == "ID":
            name = self.consume("ID")[1]
            return ("VAR", name)

        if tok[0] == "LPAREN":
            self.consume("LPAREN")
            expr = self.parse_expression()
            self.consume("RPAREN")
            return expr

        raise SyntaxError(f"Unexpected token in factor: {tok}")

# ------------------------
# 3. INTERPRETER + ENVIRONMENT
# ------------------------

env = {}  # variables, e.g. x, result

def eval_expr(node):
    kind = node[0]
    if kind == "NUM":
        return node[1]
    if kind == "VAR":
        name = node[1]
        return env.get(name, 0)
    if kind == "BINOP":
        op, left, right = node[1], node[2], node[3]
        lval = eval_expr(left)
        rval = eval_expr(right)
        if op == "PLUS":
            return lval + rval
        if op == "MINUS":
            return lval - rval
        if op == "TIMES":
            return lval * rval
        if op == "DIV":
            return lval / rval
    raise RuntimeError(f"Unknown expression node: {node}")

def eval_condition(node):
    _, op, left, right = node
    lval = eval_expr(left)
    rval = eval_expr(right)
    if op == "GT":
        return lval > rval
    if op == "LT":
        return lval < rval
    if op == "GE":
        return lval >= rval
    if op == "LE":
        return lval <= rval
    if op == "EQ":
        return lval == rval
    raise RuntimeError(f"Unknown condition op: {op}")

def do_sort(obj):
    print(f"[SORT] (demo) Sorting {obj}...")

def do_print(value):
    print(f"[PRINT] {value}")

def do_compute(expr_node):
    val = eval_expr(expr_node)
    env["result"] = val
    print(f"[COMPUTE] result = {val}")

def execute(node):
    kind = node[0]

    if kind == "ASSIGN":
        _, name, expr = node
        val = eval_expr(expr)
        env[name] = val
        print(f"[ASSIGN] {name} = {val}")
        return

    if kind == "IF":
        _, cond, body = node
        if eval_condition(cond):
            print("[IF] condition true, executing body")
            execute(body)
        else:
            print("[IF] condition false, skipping body")
        return

    if kind == "ACTION_CMD":
        _, action, obj, expr = node
        if action == "sort":
            do_sort(obj or "numbers")
        elif action in ("print", "show"):
            # if "print result", use env["result"]
            if obj == "result":
                do_print(env.get("result", None))
            else:
                do_print(obj)
        elif action == "compute":
            do_compute(expr)
        return

    raise RuntimeError(f"Unknown AST node: {node}")

# ------------------------
# 4. SIMPLE REPL FOR DEMO
# ------------------------

if __name__ == "__main__":
    print("HybridMind core demo (no LLM, no concurrency). Type 'exit' to quit.")
    while True:
        text = input(">>> ")
        if text.strip() == "exit":
            break
        try:
            tokens = tokenize(text)
            parser = Parser(tokens)
            ast = parser.parse_command()
            print("AST:", ast)
            execute(ast)
        except Exception as e:
            print("Error:", e)
