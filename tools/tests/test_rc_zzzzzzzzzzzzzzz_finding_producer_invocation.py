from __future__ import annotations

import ast
import unittest
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import rc_finding_code_contracts_base as finding_base
import rc_reachability_semantics as reachability
import test_rc_zzzzzzzzzzzzz_execution_prerequisite_composition as execution_composition  # noqa: F401


@dataclass(frozen=True)
class InvocationContract:
    producers: frozenset[str]
    reachable: frozenset[str]
    roots: frozenset[str]
    edges: tuple[tuple[str, str], ...]


class _FindingConstructorVisitor(ast.NodeVisitor):
    """Detect Finding(...) construction in one top-level function body."""

    def __init__(self, root: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.root = root
        self.found = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node is self.root:
            for statement in node.body:
                self.visit(statement)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if node is self.root:
            for statement in node.body:
                self.visit(statement)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        # Lambda bodies are separate deferred execution scopes.
        return

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "Finding":
            self.found = True
            return
        self.generic_visit(node)


class _ExpressionInvocationVisitor(ast.NodeVisitor):
    """Collect same-module calls and direct callback references in an expression."""

    def __init__(self, function_names: set[str]) -> None:
        self.function_names = function_names
        self.calls: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in self.function_names:
            self.calls.add(node.func.id)

        # Stable tool entry points hand `run` to execute_tool as a callback.
        # Treat a same-module function passed directly as an argument/keyword as
        # an invocation edge, not as inert data.
        for argument in node.args:
            if isinstance(argument, ast.Name) and argument.id in self.function_names:
                self.calls.add(argument.id)
        for keyword in node.keywords:
            if (
                keyword.arg is not None
                and isinstance(keyword.value, ast.Name)
                and keyword.value.id in self.function_names
            ):
                self.calls.add(keyword.value.id)

        self.visit(node.func)
        for argument in node.args:
            self.visit(argument)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        # Definition evaluates defaults but not the body.
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        # Creating a generator evaluates only the outermost iterable. Its body,
        # filters, and later iterables remain deferred until iteration.
        if node.generators:
            self.visit(node.generators[0].iter)



def _expression_calls(node: ast.AST | None, function_names: set[str]) -> set[str]:
    if node is None:
        return set()
    visitor = _ExpressionInvocationVisitor(function_names)
    visitor.visit(node)
    return visitor.calls


def _definition_time_calls(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    function_names: set[str],
) -> set[str]:
    calls: set[str] = set()
    for expression in (
        *node.decorator_list,
        *node.args.defaults,
        *node.args.kw_defaults,
    ):
        calls.update(_expression_calls(expression, function_names))
    if node.returns is not None:
        calls.update(_expression_calls(node.returns, function_names))
    return calls


def _block_calls(
    statements: list[ast.stmt],
    function_names: set[str],
    constants: dict[str, Any] | None = None,
) -> set[str]:
    calls: set[str] = set()
    state = dict(constants or {})

    for statement in statements:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls.update(_definition_time_calls(statement, function_names))
        elif isinstance(statement, ast.ClassDef):
            for expression in (*statement.decorator_list, *statement.bases):
                calls.update(_expression_calls(expression, function_names))
            for keyword in statement.keywords:
                calls.update(_expression_calls(keyword.value, function_names))
        elif isinstance(statement, ast.If):
            calls.update(_expression_calls(statement.test, function_names))
            truth = reachability.static_truth(statement.test, state)
            if truth is True:
                calls.update(_block_calls(statement.body, function_names, state))
            elif truth is False:
                calls.update(_block_calls(statement.orelse, function_names, state))
            else:
                calls.update(_block_calls(statement.body, function_names, state))
                calls.update(_block_calls(statement.orelse, function_names, state))
        elif isinstance(statement, ast.While):
            calls.update(_expression_calls(statement.test, function_names))
            truth = reachability.static_truth(statement.test, state)
            if truth is not False:
                calls.update(_block_calls(statement.body, function_names, state))
            calls.update(_block_calls(statement.orelse, function_names, state))
        elif isinstance(statement, (ast.For, ast.AsyncFor)):
            calls.update(_expression_calls(statement.iter, function_names))
            calls.update(_block_calls(statement.body, function_names, state))
            calls.update(_block_calls(statement.orelse, function_names, state))
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            for item in statement.items:
                calls.update(_expression_calls(item.context_expr, function_names))
            calls.update(_block_calls(statement.body, function_names, state))
        elif isinstance(statement, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            calls.update(_block_calls(statement.body, function_names, state))
            for handler in statement.handlers:
                calls.update(_expression_calls(handler.type, function_names))
                calls.update(_block_calls(handler.body, function_names, state))
            calls.update(_block_calls(statement.orelse, function_names, state))
            calls.update(_block_calls(statement.finalbody, function_names, state))
        elif isinstance(statement, ast.Match):
            calls.update(_expression_calls(statement.subject, function_names))
            for case in statement.cases:
                calls.update(_expression_calls(case.guard, function_names))
                if case.guard is None or reachability.static_truth(case.guard, state) is not False:
                    calls.update(_block_calls(case.body, function_names, state))
        elif isinstance(statement, ast.Expr):
            calls.update(_expression_calls(statement.value, function_names))
        elif isinstance(statement, ast.Assign):
            calls.update(_expression_calls(statement.value, function_names))
        elif isinstance(statement, ast.AnnAssign):
            calls.update(_expression_calls(statement.value, function_names))
        elif isinstance(statement, ast.AugAssign):
            calls.update(_expression_calls(statement.value, function_names))
        elif isinstance(statement, ast.Return):
            calls.update(_expression_calls(statement.value, function_names))
        elif isinstance(statement, ast.Raise):
            calls.update(_expression_calls(statement.exc, function_names))
            calls.update(_expression_calls(statement.cause, function_names))
        elif isinstance(statement, ast.Assert):
            calls.update(_expression_calls(statement.test, function_names))
            calls.update(_expression_calls(statement.msg, function_names))

        reachability.update_known_constants(statement, state)
        if reachability.statement_always_terminates(statement, state):
            break

    return calls


def invocation_contract(source: str) -> InvocationContract:
    tree = ast.parse(source)
    definitions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    function_names = set(definitions)

    producers: set[str] = set()
    graph: dict[str, set[str]] = {}
    for name, definition in definitions.items():
        finder = _FindingConstructorVisitor(definition)
        finder.visit(definition)
        if finder.found:
            producers.add(name)
        graph[name] = _block_calls(definition.body, function_names)

    roots = _block_calls(tree.body, function_names)
    if "main" in definitions:
        roots.add("main")
    elif "run" in definitions:
        roots.add("run")

    reachable: set[str] = set()
    queue: deque[str] = deque(sorted(roots & function_names))
    while queue:
        current = queue.popleft()
        if current in reachable:
            continue
        reachable.add(current)
        queue.extend(sorted(graph.get(current, set()) - reachable))

    edges = tuple(
        sorted(
            (caller, callee)
            for caller, callees in graph.items()
            if caller in reachable
            for callee in callees
        )
    )
    return InvocationContract(
        producers=frozenset(producers),
        reachable=frozenset(producers & reachable),
        roots=frozenset(roots),
        edges=edges,
    )


def producer_invocation_findings(
    published_source: str,
    candidate_source: str,
    source_path: str,
) -> list[str]:
    published = invocation_contract(published_source)
    candidate = invocation_contract(candidate_source)
    findings: list[str] = []
    for producer in sorted(published.reachable):
        if producer not in candidate.producers:
            findings.append(f"FINDING_PRODUCER_MISSING:{source_path}:{producer}")
        elif producer not in candidate.reachable:
            findings.append(f"FINDING_PRODUCER_UNREACHABLE:{source_path}:{producer}")
    return findings


class ReleaseCandidateFindingProducerInvocationTests(unittest.TestCase):
    def test_every_published_reachable_finding_producer_remains_invoked(self) -> None:
        checked = 0
        reachable_producers = 0
        for source_path in finding_base.published_python_paths():
            published_source = finding_base.git_source_at(
                finding_base.CHECKPOINT_COMMIT,
                source_path,
            )
            published = invocation_contract(published_source)
            if not published.reachable:
                continue

            checked += 1
            reachable_producers += len(published.reachable)
            candidate_path = finding_base.REPO_ROOT / source_path
            with self.subTest(source=source_path):
                self.assertTrue(candidate_path.is_file())
                candidate_source = candidate_path.read_text(encoding="utf-8")
                self.assertEqual(
                    producer_invocation_findings(
                        published_source,
                        candidate_source,
                        source_path,
                    ),
                    [],
                )

        self.assertGreaterEqual(checked, 8)
        self.assertGreater(reachable_producers, 20)

    def test_validate_repository_licensing_producer_is_reachable_from_entrypoint(self) -> None:
        source_path = "tools/validate-standards/validate_repository.py"
        published_source = finding_base.git_source_at(
            finding_base.CHECKPOINT_COMMIT,
            source_path,
        )
        contract = invocation_contract(published_source)
        self.assertIn("validate_licensing", contract.producers)
        self.assertIn("validate_licensing", contract.reachable)
        self.assertIn(("run", "validate_licensing"), contract.edges)

        removed = published_source.replace(
            "    validate_licensing(root, findings)\n",
            "",
            1,
        )
        self.assertIn(
            f"FINDING_PRODUCER_UNREACHABLE:{source_path}:validate_licensing",
            producer_invocation_findings(
                published_source,
                removed,
                source_path,
            ),
        )

    def test_statically_false_producer_call_does_not_satisfy_reachability(self) -> None:
        published = '''
def emit(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
def run(findings):
    emit(findings)
def main():
    execute_tool(run=run)
'''
        candidate = '''
def emit(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
def run(findings):
    if False:
        emit(findings)
def main():
    execute_tool(run=run)
'''
        self.assertEqual(invocation_contract(published).reachable, frozenset({"emit"}))
        self.assertEqual(invocation_contract(candidate).reachable, frozenset())
        self.assertEqual(
            producer_invocation_findings(published, candidate, "sample.py"),
            ["FINDING_PRODUCER_UNREACHABLE:sample.py:emit"],
        )


if __name__ == "__main__":
    unittest.main()
