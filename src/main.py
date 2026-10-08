"""CLI entry point: python src/main.py [file1.scm file2.scm ...]."""

import sys
from pathlib import Path
from typing import TextIO

from environment import Environment
from evaluator import evaluate
from parser import parse
from primitives import make_global_environment
from printer import format_value
from values import SchemeError


def run(source: str, env: Environment, output: TextIO) -> None:
    for expression in parse(source):
        value = evaluate(expression, env)
        if value is not None:
            output.write(format_value(value) + "\n")


def main(arguments: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if arguments is None else arguments
    # Use deterministic UTF-8 output even on Windows with redirected streams.
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", newline="\n")
    env = make_global_environment(sys.stdout)
    try:
        if arguments:
            for filename in arguments:
                run(Path(filename).read_text(encoding="utf-8-sig"), env, sys.stdout)
        else:
            run(sys.stdin.read().lstrip("\ufeff"), env, sys.stdout)
    except (SchemeError, OSError, ArithmeticError, RecursionError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
