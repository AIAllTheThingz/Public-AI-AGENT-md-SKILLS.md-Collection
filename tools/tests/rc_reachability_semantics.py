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


def _expression_obviously_non_raising(node: ast.AST | None) -> bool:
    if node is None or isinstance(node, ast.Constant):
        return True
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(_expression_obviously_non_raising(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            (key is None or _expression_obviously_non_raising(key))
            and _expression_obviously_non_raising(value)
            for key, value in zip(node.keys, node.values)
        )
    if isinstance(node, ast.UnaryOp) and isinstance(
        node.op, (ast.UAdd, ast.USub, ast.Not, ast.Invert)
    ):
        return _expression_obviously_non_raising(node.operand)
    return False


def _block_terminates_without_raising(
    statements: list[ast.stmt], constants: dict[str, Any] | None = None
) -> bool:
    state = dict(constants or {})
    for statement in statements:
        if isinstance(statement, ast.Return):
            return _expression_obviously_non_raising(statement.value)
        if isinstance(statement, (ast.Break, ast.Continue)):
            return True
        if isinstance(statement, ast.Raise):
            return False
        if isinstance(statement, ast.If):
            truth = static_truth(statement.test, state)
            if truth is True:
                return _block_terminates_without_raising(statement.body, state)
            if truth is False:
                return bool(statement.orelse) and _block_terminates_without_raising(
                    statement.orelse, state
                )
            return bool(statement.orelse) and _block_terminates_without_raising(
                statement.body, state
            ) and _block_terminates_without_raising(statement.orelse, state)
        if isinstance(statement, ast.Pass):
            continue
        if isinstance(statement, ast.Assign):
            if not _expression_obviously_non_raising(statement.value):
                return False
            update_known_constants(statement, state)
            continue
        if isinstance(statement, ast.AnnAssign):
            if statement.value is not None and not _expression_obviously_non_raising(
                statement.value
            ):
                return False
            update_known_constants(statement, state)
            continue
        if isinstance(statement, ast.Expr) and _expression_obviously_non_raising(
            statement.value
        ):
            continue
        return False
    return False


def _block_has_reachable_outer_break(
    statements: list[ast.stmt], constants: dict[str, Any] | None = None
) -> bool:
    state = dict(constants or {})
    for statement in statements:
        if isinstance(statement, ast.Break):
            return True
        if isinstance(statement, (ast.Return, ast.Raise, ast.Continue)):
            return False

        if isinstance(statement, ast.If):
            truth = static_truth(statement.test, state)
            branches = (
                [statement.body]
                if truth is True
                else [statement.orelse]
                if truth is False
                else [statement.body, statement.orelse]
            )
            if any(
                _block_has_reachable_outer_break(branch, state)
                for branch in branches
            ):
                return True
            if statement_always_terminates(statement, state):
                return False
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            if _block_has_reachable_outer_break(statement.body, state):
                return True
            if statement_always_terminates(statement, state):
                return False
        elif isinstance(statement, ast.Try) or (
            hasattr(ast, "TryStar") and isinstance(statement, ast.TryStar)
        ):
            regions = [statement.body, statement.orelse, statement.finalbody]
            regions.extend(handler.body for handler in statement.handlers)
            if any(
                _block_has_reachable_outer_break(region, state)
                for region in regions
            ):
                return True
            if statement_always_terminates(statement, state):
                return False
        elif isinstance(statement, ast.Match):
            if any(
                _block_has_reachable_outer_break(case.body, state)
                for case in statement.cases
            ):
                return True
        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            # Breaks inside a nested loop belong to that nested loop.
            if statement_always_terminates(statement, state):
                return False

        update_known_constants(statement, state)
    return False


def loop_body_has_break(
    statements: list[ast.stmt], constants: dict[str, Any] | None = None
) -> bool:
    return _block_has_reachable_outer_break(statements, constants)


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
        if truth is True and not loop_body_has_break(node.body, constants):
            return True
    try_types = (ast.Try,) + ((ast.TryStar,) if hasattr(ast, "TryStar") else ())
    if isinstance(node, try_types):
        if node.finalbody and block_always_terminates(node.finalbody, constants):
            return True

        # If the body obviously reaches a non-raising terminal such as
        # `return None`, exception handlers are irrelevant because none can run.
        if _block_terminates_without_raising(node.body, constants):
            return True

        handlers_terminate = all(
            block_always_terminates(handler.body, constants)
            for handler in node.handlers
        )
        body_terminates = block_always_terminates(node.body, constants)
        if body_terminates:
            return handlers_terminate

        normal_path_terminates = bool(node.orelse) and block_always_terminates(
            node.orelse, constants
        )
        return normal_path_terminates and handlers_terminate
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
