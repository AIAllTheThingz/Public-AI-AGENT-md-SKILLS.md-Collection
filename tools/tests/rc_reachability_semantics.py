from __future__ import annotations

import ast
from typing import Any

UNKNOWN = object()


def static_value(node: ast.AST, constants: dict[str, Any]) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id, UNKNOWN)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        value = static_value(node.operand, constants)
        return UNKNOWN if value is UNKNOWN else not bool(value)
    if isinstance(node, ast.BoolOp):
        values = [static_value(item, constants) for item in node.values]
        if isinstance(node.op, ast.And):
            if any(value is not UNKNOWN and not bool(value) for value in values):
                return False
            if all(value is not UNKNOWN for value in values):
                return all(bool(value) for value in values)
        if isinstance(node.op, ast.Or):
            if any(value is not UNKNOWN and bool(value) for value in values):
                return True
            if all(value is not UNKNOWN for value in values):
                return any(bool(value) for value in values)
        return UNKNOWN
    if (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and len(node.comparators) == 1
    ):
        left = static_value(node.left, constants)
        right = static_value(node.comparators[0], constants)
        if left is UNKNOWN or right is UNKNOWN:
            return UNKNOWN
        operator = node.ops[0]
        if isinstance(operator, ast.Eq):
            return left == right
        if isinstance(operator, ast.NotEq):
            return left != right
        if isinstance(operator, ast.Is):
            return left is right
        if isinstance(operator, ast.IsNot):
            return left is not right
    return UNKNOWN


def static_truth(node: ast.AST, constants: dict[str, Any]) -> bool | None:
    value = static_value(node, constants)
    return None if value is UNKNOWN else bool(value)


def update_known_constants(statement: ast.stmt, constants: dict[str, Any]) -> None:
    if isinstance(statement, ast.Assign):
        value = static_value(statement.value, constants)
        for target in statement.targets:
            if isinstance(target, ast.Name):
                if value is UNKNOWN:
                    constants.pop(target.id, None)
                else:
                    constants[target.id] = value
    elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
        value = (
            UNKNOWN
            if statement.value is None
            else static_value(statement.value, constants)
        )
        if value is UNKNOWN:
            constants.pop(statement.target.id, None)
        else:
            constants[statement.target.id] = value
    elif isinstance(statement, (ast.AugAssign, ast.Delete)):
        for item in ast.walk(statement):
            if isinstance(item, ast.Name) and isinstance(item.ctx, (ast.Store, ast.Del)):
                constants.pop(item.id, None)


class _LoopBreakVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.found = False

    def visit_Break(self, node: ast.Break) -> None:
        self.found = True

    def visit_For(self, node: ast.For) -> None:
        return

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        return

    def visit_While(self, node: ast.While) -> None:
        return

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        return

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        return

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return


def loop_body_has_break(statements: list[ast.stmt]) -> bool:
    visitor = _LoopBreakVisitor()
    for statement in statements:
        visitor.visit(statement)
        if visitor.found:
            return True
    return False


def statement_always_terminates(
    node: ast.stmt, constants: dict[str, Any] | None = None
) -> bool:
    constants = {} if constants is None else constants
    if isinstance(node, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
        return True
    if isinstance(node, ast.If):
        truth = static_truth(node.test, constants)
        if truth is True:
            return block_always_terminates(node.body, constants)
        if truth is False:
            return bool(node.orelse) and block_always_terminates(
                node.orelse, constants
            )
        return bool(node.orelse) and block_always_terminates(
            node.body, constants
        ) and block_always_terminates(node.orelse, constants)
    if isinstance(node, ast.While):
        truth = static_truth(node.test, constants)
        if truth is True and not loop_body_has_break(node.body):
            return True
    return False


def block_always_terminates(
    statements: list[ast.stmt], constants: dict[str, Any] | None = None
) -> bool:
    state = dict(constants or {})
    for statement in statements:
        if statement_always_terminates(statement, state):
            return True
        update_known_constants(statement, state)
    return False
