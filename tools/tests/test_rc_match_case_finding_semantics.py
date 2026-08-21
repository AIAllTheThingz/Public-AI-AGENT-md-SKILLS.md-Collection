from __future__ import annotations

import ast
import unittest
from collections import Counter

import rc_finding_code_contracts_base as base


def _pattern_contract(pattern: ast.pattern) -> str:
    return base.canonical_ast(pattern)


def _guard_contract(guard: ast.expr | None) -> str:
    return "<no-guard>" if guard is None else base.canonical_ast(guard)


def literal_finding_codes(text: str) -> set[str]:
    tree = base.normalize_bound_names(ast.parse(text))
    result: set[str] = set()
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Finding"
        ):
            continue
        code = base.finding_code(node)
        if code is not None:
            result.add(code)
    return result


def match_case_contracts(
    text: str,
    source_path: str = "<memory>",
) -> Counter[tuple[str, str, str, tuple[str, ...]]]:
    tree = base.normalize_bound_names(ast.parse(text))
    contracts: Counter[tuple[str, str, str, tuple[str, ...]]] = Counter()

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.function = "<module>"
            self.match_context: list[str] = []

        def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            previous = self.function
            self.function = node.name
            try:
                for statement in node.body:
                    self.visit(statement)
            finally:
                self.function = previous

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self._visit_function(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self._visit_function(node)

        def visit_Match(self, node: ast.Match) -> None:
            subject = base.canonical_ast(node.subject)
            for case in node.cases:
                marker = (
                    f"subject:{subject}|pattern:{_pattern_contract(case.pattern)}|"
                    f"guard:{_guard_contract(case.guard)}"
                )
                self.match_context.append(marker)
                try:
                    for statement in case.body:
                        self.visit(statement)
                finally:
                    self.match_context.pop()

        def visit_Call(self, node: ast.Call) -> None:
            if (
                self.match_context
                and isinstance(node.func, ast.Name)
                and node.func.id == "Finding"
            ):
                code = base.finding_code(node)
                if code is not None:
                    contracts[
                        (
                            source_path,
                            self.function,
                            code,
                            tuple(self.match_context),
                        )
                    ] += 1
            self.generic_visit(node)

    Visitor().visit(tree)
    return contracts


def published_literal_codes() -> set[str]:
    result: set[str] = set()
    for relative in base.published_python_paths():
        result.update(literal_finding_codes(base.git_source_at(base.CHECKPOINT_COMMIT, relative)))
    return result


def published_match_contracts() -> Counter[tuple[str, str, str, tuple[str, ...]]]:
    result: Counter[tuple[str, str, str, tuple[str, ...]]] = Counter()
    for relative in base.published_python_paths():
        result.update(
            match_case_contracts(
                base.git_source_at(base.CHECKPOINT_COMMIT, relative),
                relative,
            )
        )
    return result


def candidate_match_contracts(
    public_codes: set[str],
) -> Counter[tuple[str, str, str, tuple[str, ...]]]:
    result: Counter[tuple[str, str, str, tuple[str, ...]]] = Counter()
    for path in base.candidate_python_paths():
        relative = path.relative_to(base.REPO_ROOT).as_posix()
        contracts = match_case_contracts(path.read_text(encoding="utf-8"), relative)
        for contract, count in contracts.items():
            if contract[2] in public_codes:
                result[contract] += count
    return result


class ReleaseCandidateMatchCaseFindingSemanticsTests(unittest.TestCase):
    def test_published_codes_keep_their_match_case_pattern_and_guard_contexts(self):
        public_codes = published_literal_codes()
        self.assertGreater(len(public_codes), 20)
        self.assertEqual(
            candidate_match_contracts(public_codes),
            published_match_contracts(),
            "published finding codes must not move into, out of, or between match/case branches without compatibility review",
        )

    def test_moving_a_finding_between_match_cases_changes_the_contract(self):
        original = '''
def validate(value):
    match value:
        case "allowed":
            Finding("PUBLIC_CODE", "message")
        case "blocked":
            pass
'''
        moved = '''
def validate(value):
    match value:
        case "allowed":
            pass
        case "blocked":
            Finding("PUBLIC_CODE", "message")
'''
        self.assertNotEqual(match_case_contracts(original), match_case_contracts(moved))

    def test_changing_a_match_guard_changes_the_contract(self):
        original = '''
def validate(value):
    match value:
        case item if item > 0:
            Finding("PUBLIC_CODE", "message")
'''
        changed = '''
def validate(value):
    match value:
        case item if item >= 0:
            Finding("PUBLIC_CODE", "message")
'''
        self.assertNotEqual(match_case_contracts(original), match_case_contracts(changed))

    def test_moving_a_finding_into_match_control_flow_is_detected(self):
        outside = '''
def validate(value):
    Finding("PUBLIC_CODE", "message")
'''
        inside = '''
def validate(value):
    match value:
        case _:
            Finding("PUBLIC_CODE", "message")
'''
        self.assertEqual(match_case_contracts(outside), Counter())
        self.assertNotEqual(match_case_contracts(outside), match_case_contracts(inside))


if __name__ == "__main__":
    unittest.main()
