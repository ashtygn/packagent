"""Safety battery for the restricted expression validator.

Proves the whitelist rejects sandbox-escape primitives (__import__,
attribute access, calls) and everything else outside the Phase 0 grammar,
while accepting the piecewise forms from the Rule IR spec.
"""

import ast
import sys

import pytest

from pkgtk.schemas.expr import MAX_EXPR_LENGTH, ExprError, evaluate, validate_expr

MALICIOUS = [
    '__import__("os").system("echo pwned")',  # import + call
    "().__class__.__mro__[1].__subclasses__()",  # attribute/subscript escape chain
    'open("secrets.txt")',  # call to builtin
    "A.__class__",  # attribute access on allowed var
    'eval("1+1")',  # eval smuggling
    "(lambda: 42)()",  # lambda + call
    "[x for x in (1, 2)]",  # comprehension
    "'a' + 'b'",  # string constants
    "A if A else A",  # conditional expression
    "A and A",  # boolean logic
    "A ** 8 ** 8 ** 8",  # pow (also DoS vector)
    "A % 2",  # mod not in grammar
    "B + 1",  # name outside allowed set
    "True",  # boolean literal
    "A := 5",  # walrus
    "1j + A",  # complex literal
]

PIECEWISE_ACCEPT = [
    "10 < A <= 14",
    "A <= 10",
    "A / 2 + 0.5",
    "-3.5 + A * 2",
    "2.0",
]


@pytest.mark.parametrize("expr", MALICIOUS)
def test_malicious_rejected(expr):
    with pytest.raises(ExprError):
        validate_expr(expr)


@pytest.mark.parametrize("expr", PIECEWISE_ACCEPT)
def test_piecewise_examples_accepted(expr):
    assert isinstance(validate_expr(expr), ast.Expression)


def test_import_never_reaches_execution():
    # mailbox is a stdlib module nothing in this test stack imports; if the
    # expression were ever executed rather than just parsed, it would appear
    # in sys.modules.
    assert "mailbox" not in sys.modules
    with pytest.raises(ExprError):
        evaluate('__import__("mailbox")', {"A": 1.0})
    assert "mailbox" not in sys.modules


def test_chained_comparison_semantics():
    assert evaluate("10 < A <= 14", {"A": 12.0}) is True
    assert evaluate("10 < A <= 14", {"A": 14.0}) is True
    assert evaluate("10 < A <= 14", {"A": 10.0}) is False
    assert evaluate("10 < A <= 14", {"A": 20.0}) is False


def test_arithmetic_evaluation():
    assert evaluate("A / 2 + 0.5", {"A": 3.0}) == 2.0
    assert evaluate("-A * 2", {"A": 1.5}) == -3.0
    assert evaluate("2.0") == 2.0


def test_unbound_variable_rejected_at_eval():
    tree = validate_expr("A + 1", allowed_vars=("A",))
    with pytest.raises(ExprError):
        evaluate(tree, {})


def test_division_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        evaluate("A / 0", {"A": 1.0})


def test_oversized_expression_rejected():
    with pytest.raises(ExprError):
        validate_expr("1 + " * (MAX_EXPR_LENGTH // 3) + "1")


def test_non_string_rejected():
    with pytest.raises(ExprError):
        validate_expr(1234)  # type: ignore[arg-type]


def test_custom_allowed_vars():
    assert evaluate("W * H", {"W": 3.0, "H": 2.0}) == 6.0
    with pytest.raises(ExprError):
        validate_expr("W * H", allowed_vars=("W",))
