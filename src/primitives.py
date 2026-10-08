"""The standard procedures required by spec section 5."""

import math
import operator
import sys
from typing import Any, TextIO

from environment import Environment
from printer import format_value
from values import (
    NIL,
    BuiltinProcedure,
    Pair,
    SchemeError,
    Symbol,
    is_number,
    is_procedure,
    list_items,
    make_list,
)


def require_numbers(*values: Any) -> None:
    if not all(is_number(value) for value in values):
        raise SchemeError("expected a number")


def require_integers(*values: Any) -> None:
    if not all(type(value) is int for value in values):
        raise SchemeError("expected an integer")


def add(*values: Any) -> Any:
    require_numbers(*values)
    return sum(values)


def subtract(first: Any, *rest: Any) -> Any:
    require_numbers(first, *rest)
    if not rest:
        return -first
    result = first
    for value in rest:
        result -= value
    return result


def multiply(*values: Any) -> Any:
    require_numbers(*values)
    return math.prod(values)


def quotient(dividend: Any, divisor: Any) -> int:
    require_integers(dividend, divisor)
    if divisor == 0:
        raise SchemeError("division by zero")
    # Integer arithmetic avoids loss of precision for large integers.
    magnitude = abs(dividend) // abs(divisor)
    return -magnitude if (dividend < 0) != (divisor < 0) else magnitude


def divide(first: Any, *rest: Any) -> Any:
    require_numbers(first, *rest)
    if not rest:
        if first == 0:
            raise SchemeError("division by zero")
        return 1 / first
    result = first
    for value in rest:
        if value == 0:
            raise SchemeError("division by zero")
        if type(result) is int and type(value) is int:
            result = quotient(result, value)
        else:
            result /= value
    return result


def modulo(dividend: Any, divisor: Any) -> int:
    require_integers(dividend, divisor)
    if divisor == 0:
        raise SchemeError("division by zero")
    return dividend % divisor


def numeric_function(function):
    def checked(*values):
        require_numbers(*values)
        return function(*values)

    return checked


def comparison(function):
    def compare(*values):
        if not (
            all(is_number(value) for value in values)
            or all(isinstance(value, Symbol) for value in values)
        ):
            raise SchemeError("comparison expects numbers or symbols")
        return all(function(left, right) for left, right in zip(values, values[1:]))

    return compare


def car(value: Any) -> Any:
    if not isinstance(value, Pair):
        raise SchemeError("car: expected a pair")
    return value.car


def cdr(value: Any) -> Any:
    if not isinstance(value, Pair):
        raise SchemeError("cdr: expected a pair")
    return value.cdr


def is_list(value: Any) -> bool:
    while isinstance(value, Pair):
        value = value.cdr
    return value is NIL


def append(*values: Any) -> Any:
    if not values:
        return NIL
    # Copy the prefixes and preserve the final tail, as Scheme append does.
    prefixes = []
    for value in values[:-1]:
        prefixes.extend(list_items(value))
    return make_list(prefixes, values[-1])


def eq(left: Any, right: Any) -> bool:
    if is_number(left) and is_number(right):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, Symbol) or type(left) is bool:
        return left == right
    return left is right


def equal(left: Any, right: Any) -> bool:
    # An explicit stack also handles long lists without Python recursion.
    pending = [(left, right)]
    while pending:
        left, right = pending.pop()
        if isinstance(left, Pair) and isinstance(right, Pair):
            pending.extend(((left.car, right.car), (left.cdr, right.cdr)))
        elif type(left) is str and type(right) is str:
            if left != right:
                return False
        elif not eq(left, right):
            return False
    return True


def make_global_environment(output: TextIO | None = None) -> Environment:
    environment = Environment()
    output = sys.stdout if output is None else output

    def register(name, function, minimum=0, maximum=None):
        environment.define(
            Symbol(name), BuiltinProcedure(name, function, minimum, maximum)
        )

    def display(value):
        output.write(format_value(value, display=True))

    def newline():
        output.write("\n")

    register("+", add)
    register("-", subtract, 1)
    register("*", multiply)
    register("/", divide, 1)
    register("modulo", modulo, 2, 2)
    register("quotient", quotient, 2, 2)
    register("expt", numeric_function(pow), 2, 2)
    register("abs", numeric_function(abs), 1, 1)
    for name, function in (
        ("=", operator.eq),
        ("<", operator.lt),
        (">", operator.gt),
        ("<=", operator.le),
        (">=", operator.ge),
    ):
        register(name, comparison(function), 2)
    register("not", lambda value: value is False, 1, 1)
    register("cons", Pair, 2, 2)
    register("car", car, 1, 1)
    register("cdr", cdr, 1, 1)
    register("list", lambda *values: make_list(values))
    register("length", lambda value: len(list_items(value)), 1, 1)
    register("append", append)
    register("null?", lambda value: value is NIL, 1, 1)
    register("pair?", lambda value: isinstance(value, Pair), 1, 1)
    register("list?", is_list, 1, 1)
    register("number?", is_number, 1, 1)
    register("boolean?", lambda value: type(value) is bool, 1, 1)
    register("symbol?", lambda value: isinstance(value, Symbol), 1, 1)
    register("string?", lambda value: type(value) is str, 1, 1)
    register("procedure?", is_procedure, 1, 1)
    register("zero?", numeric_function(lambda value: value == 0), 1, 1)
    register("even?", numeric_function(lambda value: value % 2 == 0), 1, 1)
    register("odd?", numeric_function(lambda value: value % 2 != 0), 1, 1)
    register("eq?", eq, 2, 2)
    register("equal?", equal, 2, 2)
    register("display", display, 1, 1)
    register("newline", newline, 0, 0)
    return environment
