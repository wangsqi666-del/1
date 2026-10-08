"""Lexical environments: local bindings plus a reference to an outer scope."""

from typing import Any

from values import SchemeError, Symbol


class Environment:
    def __init__(self, outer: "Environment | None" = None):
        self.bindings: dict[Symbol, Any] = {}
        self.outer = outer

    def define(self, name: Symbol, value: Any) -> None:
        self.bindings[name] = value

    def lookup(self, name: Symbol) -> Any:
        environment = self
        while environment is not None:
            if name in environment.bindings:
                return environment.bindings[name]
            environment = environment.outer
        raise SchemeError(f"undefined name: {name}")
