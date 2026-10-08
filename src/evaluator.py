"""Evaluate special forms and procedure calls in lexical environments."""

from typing import Any

from environment import Environment
from values import (
    NIL,
    BuiltinProcedure,
    Closure,
    Pair,
    SchemeError,
    Symbol,
    is_true,
    list_items,
)


def check_arity(name: str, arguments: list, minimum: int, maximum=None) -> None:
    if len(arguments) < minimum or (
        maximum is not None and len(arguments) > maximum
    ):
        raise SchemeError(f"{name}: wrong number of operands")


def validate_names(names: list[Any], *, unique: bool = True) -> tuple[Symbol, ...]:
    if not all(isinstance(name, Symbol) for name in names):
        raise SchemeError("expected a symbol for each parameter or binding")
    if unique and len(set(names)) != len(names):
        raise SchemeError("duplicate parameter or binding name")
    return tuple(names)


def make_closure(parameters: Any, body: list[Any], env: Environment) -> Closure:
    if not body:
        raise SchemeError("a function must have a body")
    return Closure(validate_names(list_items(parameters)), tuple(body), env)


def evaluate_sequence(expressions, env: Environment) -> Any:
    result = None
    for expression in expressions:
        result = evaluate(expression, env)
    return result


def apply(procedure: Any, arguments: list[Any]) -> Any:
    if isinstance(procedure, BuiltinProcedure):
        return procedure.call(arguments)
    if isinstance(procedure, Closure):
        if len(arguments) != len(procedure.parameters):
            raise SchemeError(
                f"function expected {len(procedure.parameters)} arguments, "
                f"got {len(arguments)}"
            )
        # Capture the definition environment, never the caller's environment.
        local = Environment(procedure.environment)
        for name, value in zip(procedure.parameters, arguments):
            local.define(name, value)
        return evaluate_sequence(procedure.body, local)
    raise SchemeError("attempted to call a value that is not a procedure")


def evaluate(expression: Any, env: Environment) -> Any:
    if isinstance(expression, Symbol):
        return env.lookup(expression)
    if expression is NIL:
        raise SchemeError("an empty list is not a function call; use '()")
    if not isinstance(expression, Pair):
        return expression

    forms = list_items(expression)
    head, arguments = forms[0], forms[1:]
    if isinstance(head, Symbol):
        if head == "quote":
            check_arity("quote", arguments, 1, 1)
            return arguments[0]
        if head == "if":
            check_arity("if", arguments, 2, 3)
            if is_true(evaluate(arguments[0], env)):
                return evaluate(arguments[1], env)
            return evaluate(arguments[2], env) if len(arguments) == 3 else None
        if head == "cond":
            for clause in arguments:
                parts = list_items(clause)
                if not parts:
                    raise SchemeError("cond: empty clause")
                test = parts[0]
                value = (
                    True
                    if isinstance(test, Symbol) and test == "else"
                    else evaluate(test, env)
                )
                if is_true(value):
                    return evaluate_sequence(parts[1:], env) if len(parts) > 1 else value
            return None
        if head == "and":
            result = True
            for argument in arguments:
                result = evaluate(argument, env)
                if not is_true(result):
                    return False
            return result
        if head == "or":
            for argument in arguments:
                result = evaluate(argument, env)
                if is_true(result):
                    return result
            return False
        if head == "define":
            check_arity("define", arguments, 2)
            target = arguments[0]
            if isinstance(target, Symbol):
                check_arity("define", arguments, 2, 2)
                value = evaluate(arguments[1], env)
                name = target
            elif isinstance(target, Pair) and isinstance(target.car, Symbol):
                name = target.car
                value = make_closure(target.cdr, arguments[1:], env)
            else:
                raise SchemeError("define: expected a name or function signature")
            # Closures retain env itself, so this binding enables recursion.
            env.define(name, value)
            return name
        if head == "lambda":
            check_arity("lambda", arguments, 2)
            return make_closure(arguments[0], arguments[1:], env)
        if head == "let":
            check_arity("let", arguments, 2)
            bindings = []
            for binding in list_items(arguments[0]):
                parts = list_items(binding)
                check_arity("let binding", parts, 2, 2)
                bindings.append(parts)
            names = validate_names(
                [binding[0] for binding in bindings], unique=False
            )
            # All initializers see the outer scope: let bindings are parallel.
            values = [evaluate(binding[1], env) for binding in bindings]
            local = Environment(env)
            # Repeated let names use the last value; initializers remain parallel.
            for name, value in zip(names, values):
                local.define(name, value)
            return evaluate_sequence(arguments[1:], local)
        if head == "begin":
            return evaluate_sequence(arguments, env)

    procedure = evaluate(head, env)
    values = [evaluate(argument, env) for argument in arguments]
    return apply(procedure, values)
