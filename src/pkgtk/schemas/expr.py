"""Restricted arithmetic expression validator for Rule IR values/conditions.

Grammar (per Phase 0 spec): numeric literals, design variables from an
allowed set (e.g. ``A``), the operators ``+ - * /``, unary minus, and
(chained) comparisons ``< <= > >= == !=``. Examples: ``A/2 + 0.5``,
``10 < A <= 14``.

Implementation is ``ast.parse`` plus a node whitelist. Anything outside the
whitelist — calls, attribute access, subscripts, names not in the allowed
set, strings, boolean logic, ``**``, ``%`` — is rejected with ``ExprError``.
Evaluation walks the validated AST directly. ``eval`` is never used.
"""

import ast
from collections.abc import Iterable, Mapping

MAX_EXPR_LENGTH = 256

_BIN_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}

_CMP_OPS = {
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
}


class ExprError(ValueError):
    """Raised when an expression falls outside the restricted grammar."""


def validate_expr(expr: str, allowed_vars: Iterable[str] = ("A",)) -> ast.Expression:
    """Parse ``expr`` and reject any node outside the whitelist.

    Returns the parsed ``ast.Expression`` for use by :func:`evaluate`.
    """
    if not isinstance(expr, str):
        raise ExprError(f"expression must be a string, got {type(expr).__name__}")
    if len(expr) > MAX_EXPR_LENGTH:
        raise ExprError(f"expression longer than {MAX_EXPR_LENGTH} characters")
    allowed = frozenset(allowed_vars)
    try:
        tree = ast.parse(expr, mode="eval")
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise ExprError(f"unparseable expression: {expr!r}") from exc
    for node in ast.walk(tree):
        _check_node(node, allowed)
    return tree


def _check_node(node: ast.AST, allowed: frozenset[str]) -> None:
    match node:
        case ast.Expression() | ast.Load():
            pass
        case ast.Constant(value=bool()):
            raise ExprError("boolean literals are not allowed")
        case ast.Constant(value=int() | float()):
            pass
        case ast.Name(id=name, ctx=ast.Load()):
            if name not in allowed:
                raise ExprError(
                    f"unknown variable {name!r} (allowed: {sorted(allowed)})"
                )
        case ast.UnaryOp(op=ast.USub()):
            pass
        case ast.BinOp(op=op) if type(op) in _BIN_OPS:
            pass
        case ast.Compare(ops=ops) if all(type(op) in _CMP_OPS for op in ops):
            pass
        case ast.USub() | ast.Add() | ast.Sub() | ast.Mult() | ast.Div():
            pass
        case ast.Lt() | ast.LtE() | ast.Gt() | ast.GtE() | ast.Eq() | ast.NotEq():
            pass
        case _:
            raise ExprError(f"disallowed syntax: {type(node).__name__}")


def evaluate(
    expr: str | ast.Expression,
    variables: Mapping[str, float] | None = None,
) -> float | bool:
    """Evaluate a validated expression by walking its AST (never ``eval``).

    ``variables`` supplies both the allowed-name set (when ``expr`` is a
    string) and the values. Division by zero raises ``ZeroDivisionError``.
    """
    variables = variables or {}
    tree = validate_expr(expr, variables) if isinstance(expr, str) else expr
    return _eval_node(tree.body, variables)


def _eval_node(node: ast.AST, variables: Mapping[str, float]) -> float | bool:
    match node:
        case ast.Constant(value=value):
            return value
        case ast.Name(id=name):
            try:
                return variables[name]
            except KeyError:
                raise ExprError(f"no value bound for variable {name!r}") from None
        case ast.UnaryOp(op=ast.USub(), operand=operand):
            return -_eval_node(operand, variables)
        case ast.BinOp(left=left, op=op, right=right):
            return _BIN_OPS[type(op)](
                _eval_node(left, variables), _eval_node(right, variables)
            )
        case ast.Compare(left=left, ops=ops, comparators=comparators):
            lhs = _eval_node(left, variables)
            for op, comparator in zip(ops, comparators, strict=True):
                rhs = _eval_node(comparator, variables)
                if not _CMP_OPS[type(op)](lhs, rhs):
                    return False
                lhs = rhs
            return True
        case _:  # unreachable after validate_expr
            raise ExprError(f"disallowed syntax: {type(node).__name__}")
