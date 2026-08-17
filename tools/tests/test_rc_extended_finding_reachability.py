from __future__ import annotations

import ast
import unittest
from collections import Counter

import test_rc_finding_reachability as _base
from rc_reachability_semantics import (
    statement_always_terminates,
    static_truth,
    update_known_constants,
)


class ExtendedReachableFindingVisitor(ast.NodeVisitor):
    def __init__(self, source_path: str) -> None:
        self.source_path = source_path
        self.function = "<module>"
        self.constants = {}
        self.contracts: Counter[tuple[str, str, str]] = Counter()

    def _visit_block(self, statements: list[ast.stmt]) -> None:
        previous = self.constants
        self.constants = dict(previous)
        try:
            for statement in statements:
                self.visit(statement)
                if statement_always_terminates(statement, self.constants):
                    break
                update_known_constants(statement, self.constants)
        finally:
            self.constants = previous

    def visit_Module(self, node: ast.Module) -> None:
        for statement in node.body:
            self.visit(statement)
            if statement_always_terminates(statement, self.constants):
                break
            update_known_constants(statement, self.constants)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        previous_function = self.function
        previous_constants = self.constants
        self.function = node.name
        self.constants = dict(previous_constants)
        try:
            for statement in node.body:
                self.visit(statement)
                if statement_always_terminates(statement, self.constants):
                    break
                update_known_constants(statement, self.constants)
        finally:
            self.function = previous_function
            self.constants = previous_constants

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        truth = static_truth(node.test, self.constants)
        if truth is True:
            self._visit_block(node.body)
        elif truth is False:
            self._visit_block(node.orelse)
        else:
            self._visit_block(node.body)
            self._visit_block(node.orelse)

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        self._visit_block(node.body)
        self._visit_block(node.orelse)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit(node.iter)
        self._visit_block(node.body)
        self._visit_block(node.orelse)

    def visit_While(self, node: ast.While) -> None:
        self.visit(node.test)
        truth = static_truth(node.test, self.constants)
        if truth is not False:
            self._visit_block(node.body)
        if truth is not True:
            self._visit_block(node.orelse)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            self.visit(item.context_expr)
        self._visit_block(node.body)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for item in node.items:
            self.visit(item.context_expr)
        self._visit_block(node.body)

    def visit_Try(self, node: ast.Try) -> None:
        self._visit_block(node.body)
        for handler in node.handlers:
            if handler.type is not None:
                self.visit(handler.type)
            self._visit_block(handler.body)
        self._visit_block(node.orelse)
        self._visit_block(node.finalbody)

    def visit_Match(self, node: ast.Match) -> None:
        self.visit(node.subject)
        for case in node.cases:
            if case.guard is not None:
                self.visit(case.guard)
            self._visit_block(case.body)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "Finding":
            code = _base.literal_finding_code(node)
            if code is not None:
                self.contracts[(self.source_path, self.function, code)] += 1
        self.generic_visit(node)


def reachable_contracts(text: str, source_path: str):
    visitor = ExtendedReachableFindingVisitor(source_path)
    visitor.visit(ast.parse(text))
    return visitor.contracts


def published_contracts():
    result = Counter()
    for relative in _base.published_python_paths():
        result.update(
            reachable_contracts(
                _base.git_source_at(_base.CHECKPOINT_COMMIT, relative), relative
            )
        )
    return result


def candidate_contracts():
    result = Counter()
    for path in _base.candidate_python_paths():
        relative = path.relative_to(_base.REPO_ROOT).as_posix()
        result.update(reachable_contracts(path.read_text(encoding="utf-8"), relative))
    return result


class ReleaseCandidateExtendedFindingReachabilityTests(unittest.TestCase):
    def test_every_published_literal_finding_survives_extended_reachability(self):
        published = published_contracts()
        candidate = candidate_contracts()
        missing = {
            contract: count - candidate.get(contract, 0)
            for contract, count in published.items()
            if candidate.get(contract, 0) < count
        }
        self.assertEqual(missing, {})

    def test_statically_infinite_loop_suppresses_following_finding(self):
        source = '''
def validate(value):
    while True:
        continue
    Finding("PUBLIC_CODE", "unreachable")
'''
        self.assertEqual(reachable_contracts(source, "sample.py"), Counter())

    def test_constant_true_infinite_loop_suppresses_following_finding(self):
        source = '''
KEEP_SPINNING = True
def validate(value):
    while KEEP_SPINNING:
        pass
    Finding("PUBLIC_CODE", "unreachable")
'''
        self.assertEqual(reachable_contracts(source, "sample.py"), Counter())

    def test_loop_with_possible_break_keeps_following_finding_reachable(self):
        source = '''
def validate(value):
    while True:
        if value:
            break
    Finding("PUBLIC_CODE", "reachable")
'''
        contracts = reachable_contracts(source, "sample.py")
        self.assertEqual(contracts[("sample.py", "validate", "PUBLIC_CODE")], 1)


if __name__ == "__main__":
    unittest.main()
