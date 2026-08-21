from __future__ import annotations

import ast
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_final_p1_and_ci_composition as final_composition  # noqa: F401


# A Finding can be unreachable because an earlier *statement* fails, not only
# because an earlier sibling in the same expression fails. The compatibility
# identity must not, however, absorb every unrelated prior statement: doing so
# would freeze implementation details that v0.10 never promised. This layer
# records execution barriers that are concrete and independently meaningful:
# same-module helpers proven not to return normally and function-local imports,
# whose import resolution can fail before the finding is reached.


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id
    return None


def _is_explicit_process_exit(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
        return (node.func.value.id, node.func.attr) in {
            ("sys", "exit"),
            ("os", "_exit"),
        }
    return False


def _static_bool(node: ast.AST) -> bool | None:
    if isinstance(node, ast.Constant):
        if node.value is True:
            return True
        if node.value is False or node.value is None:
            return False
    return None


def _block_guaranteed_to_abort(
    statements: list[ast.stmt],
    definitions: dict[str, ast.AST],
    seen: set[str],
) -> bool:
    for statement in statements:
        if isinstance(statement, ast.Raise):
            return True
        if isinstance(statement, ast.Return):
            return False
        if isinstance(statement, ast.Expr):
            if _is_explicit_process_exit(statement.value):
                return True
            helper_name = _call_name(statement.value)
            if helper_name and _helper_guaranteed_to_abort(
                helper_name,
                definitions,
                seen,
            ):
                return True
        if isinstance(statement, ast.If):
            truth = _static_bool(statement.test)
            if truth is True:
                if _block_guaranteed_to_abort(statement.body, definitions, seen):
                    return True
                continue
            if truth is False:
                if _block_guaranteed_to_abort(statement.orelse, definitions, seen):
                    return True
                continue
            if statement.body and statement.orelse:
                if _block_guaranteed_to_abort(
                    statement.body,
                    definitions,
                    seen,
                ) and _block_guaranteed_to_abort(
                    statement.orelse,
                    definitions,
                    seen,
                ):
                    return True
        # Other statements may raise at runtime, but without proof they are not
        # allowed to perturb the published compatibility identity.
    return False


def _helper_guaranteed_to_abort(
    name: str,
    definitions: dict[str, ast.AST],
    seen: set[str] | None = None,
) -> bool:
    definition = definitions.get(name)
    # Calling async def merely constructs a coroutine until it is awaited, so it
    # is not a synchronous pre-emission blocker at this call site.
    if not isinstance(definition, ast.FunctionDef):
        return False

    active = set(seen or ())
    if name in active:
        return False
    active.add(name)

    body = list(definition.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    return _block_guaranteed_to_abort(body, definitions, active)


def _literal_blocking_prerequisite(visitor, statement: ast.stmt) -> ast.AST | None:
    # Module-scope imports already participate in module initialization and
    # constructor/dependency provenance. The review gap is an import inserted in
    # an executing function immediately before an emission.
    if visitor.function != "<module>" and isinstance(
        statement,
        (ast.Import, ast.ImportFrom),
    ):
        return statement
    if not isinstance(statement, ast.Expr):
        return None
    helper_name = _call_name(statement.value)
    if helper_name is None:
        return None
    if _helper_guaranteed_to_abort(helper_name, visitor.module_definitions):
        return statement.value
    return None


def _parameterized_blocking_prerequisite(
    visitor,
    statement: ast.stmt,
) -> ast.AST | None:
    if visitor.caller != "<module>" and isinstance(
        statement,
        (ast.Import, ast.ImportFrom),
    ):
        return statement
    if not isinstance(statement, ast.Expr):
        return None
    helper_name = _call_name(statement.value)
    if helper_name is None:
        return None
    if _helper_guaranteed_to_abort(helper_name, visitor.definitions):
        return statement.value
    return None


def _prerequisite_marker(node: ast.AST) -> str:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return f"statement:requires-prior-execution:{literal_base.canonical_ast(node)}"
    return "statement:requires-prior-execution"


def _visit_block_with_statement_prerequisites(self, statements: list[ast.stmt]) -> None:
    blocker: ast.AST | None = None
    for statement in statements:
        if blocker is None:
            self.visit(statement)
        else:
            self.context.append(_prerequisite_marker(blocker))
            self.context_nodes.append(blocker)
            try:
                self.visit(statement)
            finally:
                self.context_nodes.pop()
                self.context.pop()

        candidate = _literal_blocking_prerequisite(self, statement)
        if candidate is not None:
            blocker = candidate


literal_base.FindingSignatureVisitor._visit_block = _visit_block_with_statement_prerequisites


_parameterized_visitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor


def _parameterized_visit_block_with_statement_prerequisites(
    self,
    statements: list[ast.stmt],
) -> None:
    blocker: ast.AST | None = None
    for statement in statements:
        if blocker is None:
            self.visit(statement)
        else:
            self.context_nodes.append(
                (_prerequisite_marker(blocker), blocker)
            )
            try:
                self.visit(statement)
            finally:
                self.context_nodes.pop()

        candidate = _parameterized_blocking_prerequisite(self, statement)
        if candidate is not None:
            blocker = candidate


_parameterized_visitor._visit_block = _parameterized_visit_block_with_statement_prerequisites
parameterized_active.base.ParameterizedCallSiteVisitor = _parameterized_visitor


_reachable_parameterized_visitor = (
    parameterized_reachability.ReachableParameterizedCallSiteVisitor
)


def _reachable_parameterized_visit_block_with_statement_prerequisites(
    self,
    statements: list[ast.stmt],
) -> None:
    previous_constants = self.constants
    self.constants = dict(previous_constants)
    blocker: ast.AST | None = None
    try:
        for statement in statements:
            if blocker is None:
                self.visit(statement)
            else:
                self.context_nodes.append(
                    (_prerequisite_marker(blocker), blocker)
                )
                try:
                    self.visit(statement)
                finally:
                    self.context_nodes.pop()

            candidate = _parameterized_blocking_prerequisite(self, statement)
            if candidate is not None:
                blocker = candidate

            if parameterized_reachability.statement_always_terminates(
                statement,
                self.constants,
            ):
                break
            parameterized_reachability.update_known_constants(
                statement,
                self.constants,
            )
    finally:
        self.constants = previous_constants


_reachable_parameterized_visitor._visit_block = (
    _reachable_parameterized_visit_block_with_statement_prerequisites
)


class ReleaseCandidatePreEmissionStatementPrerequisiteTests(unittest.TestCase):
    def test_raising_helper_statement_changes_literal_contract(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def explode():
    raise RuntimeError("stop")

def run(findings):
    explode()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(preceded)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any(
                "statement:requires-prior-execution" in signature
                and "explode" in signature
                for signature in actual["PUBLIC_CODE"]
            )
        )

    def test_raising_helper_statement_changes_sink_contract(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def explode():
    raise RuntimeError("stop")

def run(findings):
    explode()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(preceded),
        )

    def test_raising_helper_statement_changes_parameterized_contract(self) -> None:
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        preceded = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def explode():
    raise RuntimeError("stop")
def validate(root, findings):
    explode()
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertNotEqual(
            parameterized_active.parameterized_finding_contracts(
                direct,
                "sample.py",
            ),
            parameterized_active.parameterized_finding_contracts(
                preceded,
                "sample.py",
            ),
        )
        self.assertNotEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                direct,
                "sample.py",
            ),
            parameterized_reachability.reachable_parameterized_contracts(
                preceded,
                "sample.py",
            ),
        )

    def test_function_local_import_changes_literal_contract(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def run(findings):
    import definitely_missing_package
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(preceded)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any(
                "definitely_missing_package" in signature
                for signature in actual["PUBLIC_CODE"]
            )
        )

    def test_function_local_import_changes_parameterized_contract(self) -> None:
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        preceded = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    import definitely_missing_package
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertNotEqual(
            parameterized_active.parameterized_finding_contracts(
                direct,
                "sample.py",
            ),
            parameterized_active.parameterized_finding_contracts(
                preceded,
                "sample.py",
            ),
        )

    def test_normal_helper_statement_does_not_freeze_implementation_detail(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def observe():
    return 1

def run(findings):
    observe()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )

    def test_transitively_raising_helper_is_a_prerequisite(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def explode():
    raise RuntimeError("stop")
def wrapper():
    explode()
def run(findings):
    wrapper()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )


if __name__ == "__main__":
    unittest.main()
