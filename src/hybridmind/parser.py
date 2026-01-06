# src/hybridmind/parser.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


Token = Tuple[str, str]


class ParseError(SyntaxError):
    """Raised when the input token stream does not match the grammar."""
    pass


@dataclass
class ParserConfig:
    enable_concurrency: bool = True


class Parser:
    def __init__(self, tokens, enable_concurrency: bool = True):
        self.tokens = tokens
        self.pos = 0
        self.enable_concurrency = enable_concurrency

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
        if self.enable_concurrency:
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

        # compute must take an expression immediately (no obj)
        if action == "compute":
            expr = self.parse_expression()
            return ("ACTION_CMD", action, None, expr)

        # other actions can take an optional obj
        obj = None
        if self.peek() and self.peek()[0] in ("OBJECT", "ID"):
            obj = self.consume(self.peek()[0])[1]

        return ("ACTION_CMD", action, obj, None)


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
