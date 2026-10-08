"""Behavior checks beyond the supplied grader, using only the public spec."""

import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from main import run
from parser import parse
from primitives import make_global_environment
from values import SchemeError


class InterpreterTests(unittest.TestCase):
    def assert_program(self, source, expected):
        output = io.StringIO()
        run(source, make_global_environment(output), output)
        self.assertEqual(output.getvalue(), expected)

    def test_negative_and_large_integer_division(self):
        self.assert_program(
            """
            (/ -7 2) (/ 7 -2) (/ -7 -2) (/ 20 3 2)
            (quotient -7 2) (quotient 7 -2) (/ 2)
            (quotient 100000000000000000000000000000000000001 3)
            (modulo -17 5) (modulo 17 -5) (+) (*) (- 9)
            """,
            "-3\n-3\n3\n3\n-3\n-3\n0.5\n"
            "33333333333333333333333333333333333333\n3\n-3\n0\n1\n-9\n",
        )

    def test_symbol_comparisons_and_case_sensitive_names(self):
        self.assert_program(
            """
            (define x 1) (define X 2) (+ x X)
            (= 'foo 'foo) (< 'a 'b 'c) (> 'c 'b 'a)
            (<= 2 2 3) (>= 3 3 2) (= 1 1.0)
            """,
            "x\nX\n3\n#t\n#t\n#t\n#t\n#t\n#t\n",
        )

    def test_only_false_is_false_and_short_circuit_has_no_side_effect(self):
        self.assert_program(
            """
            (if 0 'yes 'no) (if '() 'yes 'no) (if "" 'yes 'no)
            (not 0) (and) (or) (and #t 0 '()) (or #f "")
            (and #f (display "bad")) (or 0 (display "bad"))
            (if #f (display "bad"))
            """,
            'yes\nyes\nyes\n#f\n#t\n#f\n()\n""\n#f\n0\n',
        )

    def test_cond_test_value_sequences_and_no_match(self):
        self.assert_program(
            """
            (cond (#f (/ 1 0)) ((+ 2 3)))
            (cond (#f 9) (else (display "ok") 42))
            (cond (#f 1)) (cond) (begin)
            """,
            "5\nok42\n",
        )

    def test_closures_capture_definition_scope(self):
        self.assert_program(
            """
            (define x 10)
            (define (make-adder x) (lambda (y) (+ x y)))
            (define add3 (make-adder 3))
            (let ((x 100)) (add3 7))
            x
            (let ((x 5)) (lambda () x))
            """,
            "x\nmake-adder\nadd3\n10\n10\n#<procedure>\n",
        )

    def test_recursive_local_function_and_multiple_body_expressions(self):
        self.assert_program(
            """
            (define (outer n)
              (define (fact k) (if (= k 0) 1 (* k (fact (- k 1)))))
              (display "answer:")
              (fact n))
            (outer 6)
            ((lambda () (define x 3) (+ x 4)))
            """,
            "outer\nanswer:720\n7\n",
        )

    def test_mutual_recursion(self):
        self.assert_program(
            """
            (define (is-even n) (if (= n 0) #t (is-odd (- n 1))))
            (define (is-odd n) (if (= n 0) #f (is-even (- n 1))))
            (is-even 20) (is-odd 19)
            """,
            "is-even\nis-odd\n#t\n#t\n",
        )

    def test_parallel_let_and_shadowing(self):
        self.assert_program(
            """
            (define x 10)
            (let ((x 1) (y x)) (define z (+ x y)) z)
            x
            (let ((x 1) (x (+ x 1))) x)
            (let () 42)
            """,
            "x\n11\n10\n11\n42\n",
        )

    def test_nested_quote_and_dotted_pairs(self):
        self.assert_program(
            """
            ''x '(a (1 #t "s") ()) '(1 . 2) '(1 2 . 3)
            '(1 . (2 . ())) (cdr '(1 . 2))
            (cons '(a) '(b c))
            """,
            '(quote x)\n(a (1 #t "s") ())\n(1 . 2)\n(1 2 . 3)\n'
            '(1 2)\n2\n((a) b c)\n',
        )

    def test_list_operations_and_identity(self):
        self.assert_program(
            """
            (define xs (list 1 2))
            (eq? xs xs) (eq? xs (list 1 2))
            (eq? (cdr xs) (cdr xs)) (eq? '() (list))
            (list? (cons 1 2)) (list? '()) (pair? '())
            (length (append '(a b) '() '(c))) (append)
            (equal? (append '(1) xs) '(1 1 2))
            (eq? (cdr (append '(0) xs)) xs)
            """,
            "xs\n#t\n#f\n#t\n#t\n#f\n#t\n#f\n3\n()\n#t\n#t\n",
        )

    def test_equal_is_structural_and_distinguishes_scheme_types(self):
        self.assert_program(
            """
            (equal? '(a (1 2) . 3) (cons 'a (cons (list 1 2) 3)))
            (equal? '(1 2) '(1 3)) (equal? #t 1) (eq? #f 0)
            (equal? 'a "a") (equal? "a" "a") (equal? 1 1.0)
            """,
            "#t\n#f\n#f\n#f\n#f\n#t\n#t\n",
        )

    def test_predicates(self):
        self.assert_program(
            """
            (number? #t) (number? 3.5) (boolean? 0) (boolean? #f)
            (symbol? "x") (symbol? 'x) (string? 'x) (string? "x")
            (procedure? +) (procedure? (lambda () 1)) (procedure? 'x)
            (zero? 0) (even? -4) (odd? -3)
            """,
            "#f\n#t\n#f\n#t\n#f\n#t\n#f\n#t\n#t\n#t\n#f\n#t\n#t\n#t\n",
        )

    def test_strings_comments_and_escaping(self):
        self.assert_program(
            r'''; an ignored "quote" and parentheses ()
            "a\nb\tc\"d\\e;()'"
            (display "你好\nworld\t!") (newline)
            'hello; ignored comment
            ''',
            '"a\\nb\\tc\\"d\\\\e;()\'"\n你好\nworld\t!\nhello\n',
        )

    def test_operator_and_arguments_evaluate_left_to_right(self):
        self.assert_program(
            """
            ((begin (display "op:") +)
              (begin (display "left:") 1)
              (begin (display "right:") 2))
            """,
            "op:left:right:3\n",
        )

    def test_higher_order_filter_defined_in_scheme(self):
        self.assert_program(
            """
            (define (filter f xs)
              (cond ((null? xs) '())
                    ((f (car xs)) (cons (car xs) (filter f (cdr xs))))
                    (else (filter f (cdr xs)))))
            (filter odd? '(1 2 3 4 5))
            """,
            "filter\n(1 3 5)\n",
        )

    def test_malformed_syntax_is_rejected(self):
        for source in ("(", ")", "'", '"unfinished', "'(a . b c)"):
            with self.subTest(source=source):
                with self.assertRaises(SchemeError):
                    parse(source)

    def test_invalid_calls_report_errors(self):
        for source in ("missing", "(1 2)", "(car '())", "(+ #t 1)",
                       "((lambda (x) x))", "(/ 1 0)"):
            with self.subTest(source=source):
                with self.assertRaises(SchemeError):
                    self.assert_program(source, "")

    def test_cli_stdin_and_utf8_output(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "src" / "main.py")],
            input='(display "你好") (newline) (+ 1 2)'.encode("utf-8"),
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "你好\n3\n".encode("utf-8"))
        self.assertEqual(result.stderr, b"")

    def test_cli_multiple_files_share_the_global_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Path(folder) / "first.scm"
            second = Path(folder) / "second.scm"
            first.write_text("(define answer 40)", encoding="utf-8")
            second.write_text("(+ answer 2)", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "src" / "main.py"), str(first), str(second)],
                capture_output=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, b"answer\n42\n")


if __name__ == "__main__":
    unittest.main()
