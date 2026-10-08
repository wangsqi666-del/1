"""Runtime values shared by the reader, evaluator, and standard library."""

from dataclasses import dataclass
from typing import Any, Callable, Iterable


class SchemeError(Exception):
    """A readable syntax or runtime error in a Scheme program."""


class Symbol(str):
    """A Scheme name, distinct from a string literal."""


class EmptyList:
    __slots__ = ()


NIL = EmptyList()


@dataclass(eq=False, frozen=True, slots=True)
class Pair:
    car: Any
    cdr: Any


def make_list(items: Iterable[Any], tail: Any = NIL) -> Any:
    """Build a pair chain, optionally ending in an improper tail."""
    for item in reversed(tuple(items)):
        tail = Pair(item, tail)
    return tail


def list_items(value: Any) -> list[Any]:
    """Unpack a proper list; dotted pairs are not argument lists."""
    result = []
    while isinstance(value, Pair):
        result.append(value.car)
        value = value.cdr
    if value is not NIL:
        raise SchemeError("expected a proper list")
    return result


def is_number(value: Any) -> bool:
    # bool is an int subclass in Python, but a separate type in Scheme.
    return type(value) in (int, float)


def is_true(value: Any) -> bool:
    return value is not False


@dataclass(eq=False, slots=True)
class BuiltinProcedure:
    name: str
    function: Callable[..., Any]
    minimum: int = 0
    maximum: int | None = None

    def call(self, arguments: list[Any]) -> Any:
        count = len(arguments)
        if count < self.minimum or (
            self.maximum is not None and count > self.maximum
        ):
            if self.minimum == self.maximum:
                expected = str(self.minimum)
            elif self.maximum is None:
                expected = f"at least {self.minimum}"
            else:
                expected = f"{self.minimum} to {self.maximum}"
            raise SchemeError(
                f"{self.name}: expected {expected} arguments, got {count}"
            )
        return self.function(*arguments)


@dataclass(eq=False, slots=True)
class Closure:
    parameters: tuple[Symbol, ...]
    body: tuple[Any, ...]
    environment: Any


def is_procedure(value: Any) -> bool:
    return isinstance(value, (BuiltinProcedure, Closure))
