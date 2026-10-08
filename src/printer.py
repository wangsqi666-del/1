"""Scheme's external value representation and display representation."""

from typing import Any

from values import NIL, Pair, Symbol, is_procedure


def format_value(value: Any, *, display: bool = False) -> str:
    if value is True:
        return "#t"
    if value is False:
        return "#f"
    if value is NIL:
        return "()"
    if isinstance(value, Symbol):
        return str(value)
    if isinstance(value, str):
        if display:
            return value
        escaped = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )
        return '"' + escaped + '"'
    if isinstance(value, Pair):
        elements = []
        while isinstance(value, Pair):
            elements.append(format_value(value.car, display=display))
            value = value.cdr
        if value is not NIL:
            elements.extend((".", format_value(value, display=display)))
        return "(" + " ".join(elements) + ")"
    if is_procedure(value):
        return "#<procedure>"
    if value is None:
        return "#<unspecified>"
    return str(value)
