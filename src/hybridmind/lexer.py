import re

TOKEN_SPEC = [
    ("IF",      r"if"),
    ("THEN",    r"then"),
    ("SET",     r"set"),
    ("WHILE",   r"while"),
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
            match = re.compile(tok_re).match(text, i)
            if match:
                if tok_type != "WS":
                    tokens.append((tok_type, match.group()))
                i = match.end()
                break

        if not match:
            raise ValueError(f"Unexpected character: {text[i]}")

    return tokens
