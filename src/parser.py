"""Read tokens into atoms and pair chains; quote uses the same data model."""

import re
from typing import Any

from lexer import Token, tokenize
from values import SchemeError, Symbol, make_list


INTEGER = re.compile(r"[+-]?\d+\Z")
FLOAT = re.compile(
    r"[+-]?(?:(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+)\Z"
)


class Reader:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.index = 0

    def read(self) -> Any:
        if self.index >= len(self.tokens):
            raise SchemeError("unexpected end of source")
        token = self.tokens[self.index]
        self.index += 1
        if token.kind == "quote":
            return make_list((Symbol("quote"), self.read()))
        if token.kind == "open":
            return self.read_list()
        if token.kind == "close":
            raise SchemeError(f"unexpected ')' at position {token.position}")
        if token.kind == "string":
            return token.text
        if token.text == ".":
            raise SchemeError("a dot is only valid inside a dotted pair")
        if token.text == "#t":
            return True
        if token.text == "#f":
            return False
        if INTEGER.fullmatch(token.text):
            return int(token.text)
        if FLOAT.fullmatch(token.text):
            return float(token.text)
        return Symbol(token.text)

    def read_list(self) -> Any:
        elements = []
        while self.index < len(self.tokens):
            token = self.tokens[self.index]
            if token.kind == "close":
                self.index += 1
                return make_list(elements)
            if token.kind == "atom" and token.text == ".":
                if not elements:
                    raise SchemeError("a dotted pair must have a first element")
                self.index += 1
                tail = self.read()
                if (
                    self.index >= len(self.tokens)
                    or self.tokens[self.index].kind != "close"
                ):
                    raise SchemeError("a dotted pair must have exactly one tail")
                self.index += 1
                return make_list(elements, tail)
            elements.append(self.read())
        raise SchemeError("unclosed '('")


def parse(source: str) -> list[Any]:
    reader = Reader(tokenize(source))
    expressions = []
    while reader.index < len(reader.tokens):
        expressions.append(reader.read())
    return expressions
