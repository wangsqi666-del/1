"""Tokenize Scheme source without confusing strings with comments or names."""

from dataclasses import dataclass

from values import SchemeError


@dataclass(frozen=True, slots=True)
class Token:
    kind: str
    text: str
    position: int


def tokenize(source: str) -> list[Token]:
    tokens = []
    index = 0
    punctuation = {"(": "open", ")": "close", "'": "quote"}
    escapes = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
    while index < len(source):
        char = source[index]
        if char.isspace():
            index += 1
            continue
        if char == ";":
            while index < len(source) and source[index] not in "\r\n":
                index += 1
            continue
        if char in punctuation:
            tokens.append(Token(punctuation[char], char, index))
            index += 1
            continue
        start = index
        if char == '"':
            index += 1
            characters = []
            while index < len(source) and source[index] != '"':
                char = source[index]
                if char == "\\":
                    index += 1
                    if index >= len(source):
                        raise SchemeError(f"unfinished string at position {start}")
                    char = source[index]
                    if char not in escapes:
                        raise SchemeError(f"unknown string escape: \\{char}")
                    characters.append(escapes[char])
                else:
                    characters.append(char)
                index += 1
            if index >= len(source):
                raise SchemeError(f"unclosed string at position {start}")
            index += 1
            tokens.append(Token("string", "".join(characters), start))
            continue
        while (
            index < len(source)
            and not source[index].isspace()
            and source[index] not in "();'\""
        ):
            index += 1
        tokens.append(Token("atom", source[start:index], start))
    return tokens
