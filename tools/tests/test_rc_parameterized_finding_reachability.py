from __future__ import annotations

import ast
import json
import unittest

import test_rc_parameterized_finding_codes as _base
from rc_reachability_semantics import (
    statement_always_terminates,
    static_truth,
    update_known_constants,
)


class ReachableParameterizedCallSiteVisitor(_base.ParameterizedCallSiteVisitor):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.constants = {}

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

    def _visit_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        previous = self.constants
        self.constants = dict(previous)
        try:
            super()._visit_function(node)
        finally:
            self.constants = previous

    def visit_If(self, node: ast.If) -> None:
        truth = static_truth(node.test, self.constants)
        if truth is True:
            self._with_context(node.test, node.body)
        elif truth is False:
            if node.orelse:
                self._with_context(node.test, node.orelse)
        else:
            self._with_context(node.test, node.body)
            if node.orelse:
                self._with_context(node.test, node.orelse)

    def visit_While(self, node: ast.While) -> None:
        truth = static_truth(node.test, self.constants)
        if truth is not False:
            self._with_context(node.test, node.body)
        if truth is not True and node.orelse:
            self._with_context(node.test, node.orelse)


def reachable_parameterized_contracts(text: str, source_path: str) -> set[str]:
    tree = ast.parse(text)
    helpers = _base.parameterized_finding_parameters(tree)
    if not helpers:
        return set()
    definitions = {
        statement.name: statement
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    visitor = ReachableParameterizedCallSiteVisitor(
        source_path,
        definitions,
        helpers,
        _base.module_bindings(tree),
    )
    visitor.visit(tree)
    return visitor.contracts


def published_contracts() -> set[str]:
    result: set[str] = set()
    for relative in _base.published_python_paths():
        result.update(
            reachable_parameterized_contracts(
                _base.git_source_at(_base.CHECKPOINT_COMMIT, relative), relative
            )
        )
    return result


def candidate_contracts() -> set[str]:
    result: set[str] = set()
    for path in _base.candidate_python_paths():
        relative = path.relative_to(_base.REPO_ROOT).as_posix()
        result.update(
            reachable_parameterized_contracts(
                path.read_text(encoding="utf-8"), relative
            )
        )
    return result


class ReleaseCandidateParameterizedFindingReachabilityTests(unittest.TestCase):
    def test_every_published_parameterized_call_site_remains_reachable(self):
        published = published_contracts()
        candidate = candidate_contracts()
        self.assertGreaterEqual(len(published), 8)
        self.assertEqual(
            published - candidate,
            set(),
            "published caller-supplied finding call site became unreachable",
        )

    def test_return_and_raise_before_parameterized_call_are_detected(self):
        reachable = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        returned = reachable.replace(
            '    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")',
            '    return\n    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")',
        )
        raised = reachable.replace(
            '    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")',
            '    raise RuntimeError("stop")\n    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")',
        )
        expected = reachable_parameterized_contracts(reachable, "sample.py")
        self.assertEqual(len(expected), 1)
        self.assertEqual(reachable_parameterized_contracts(returned, "sample.py"), set())
        self.assertEqual(reachable_parameterized_contracts(raised, "sample.py"), set())

    def test_infinite_loop_before_parameterized_call_is_detected(self):
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    while True:
        continue
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(reachable_parameterized_contracts(source, "sample.py"), set())

    def test_reachable_contract_keeps_call_site_semantics(self):
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        contract = next(iter(reachable_parameterized_contracts(source, "sample.py")))
        payload = json.loads(contract)
        self.assertEqual(payload["code"], "LICENSE_ENCODING")
        self.assertIn("LICENSE", " ".join(payload["arguments"].values()))


if __name__ == "__main__":
    unittest.main()
