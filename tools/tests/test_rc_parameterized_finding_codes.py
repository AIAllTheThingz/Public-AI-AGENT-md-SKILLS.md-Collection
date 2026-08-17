from __future__ import annotations

import ast
import json

import rc_parameterized_finding_codes_base as base


class BranchAwareParameterizedCallSiteVisitor(base.ParameterizedCallSiteVisitor):
    """Preserve call-site branch polarity as part of public finding semantics."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.context_nodes: list[tuple[str, ast.AST]] = []

    def _with_context(
        self, branch: str, node: ast.AST, statements: list[ast.stmt]
    ) -> None:
        self.context_nodes.append((branch, node))
        try:
            self._visit_block(statements)
        finally:
            self.context_nodes.pop()

    def visit_If(self, node: ast.If) -> None:
        self._with_context("if:true", node.test, node.body)
        if node.orelse:
            self._with_context("if:false", node.test, node.orelse)

    def visit_For(self, node: ast.For) -> None:
        self._with_context("for:body", node.iter, node.body)
        if node.orelse:
            self._with_context("for:else", node.iter, node.orelse)

    def visit_While(self, node: ast.While) -> None:
        self._with_context("while:body", node.test, node.body)
        if node.orelse:
            self._with_context("while:else", node.test, node.orelse)

    def visit_Match(self, node: ast.Match) -> None:
        for case in node.cases:
            # Match patterns are not expressions, so encode their canonical AST as
            # a literal alongside the normalized subject and guard. This preserves
            # case identity and guard semantics without pretending a pattern is an
            # executable expression.
            marker = ast.Tuple(
                elts=[
                    node.subject,
                    ast.Constant(value=base.canonical_ast(case.pattern)),
                    case.guard if case.guard is not None else ast.Constant(value=None),
                ],
                ctx=ast.Load(),
            )
            self._with_context("match:case", marker, case.body)

    def visit_Call(self, node: ast.Call) -> None:
        if not (
            isinstance(node.func, ast.Name)
            and node.func.id in self.parameterized_helpers
        ):
            self.generic_visit(node)
            return

        helper_name = node.func.id
        definition = self.definitions[helper_name]
        for code_parameter in self.parameterized_helpers[helper_name]:
            code_argument = base.call_argument(node, definition, code_parameter)
            if code_argument is None:
                continue
            code = base.literal_string(code_argument, self.module_values)
            if code is None:
                continue

            arguments: dict[str, str] = {}
            all_parameters = base.function_parameter_order(definition) + [
                argument.arg for argument in definition.args.kwonlyargs
            ]
            for parameter in all_parameters:
                if parameter == code_parameter:
                    continue
                argument = base.call_argument(node, definition, parameter)
                if argument is None:
                    continue
                arguments[parameter] = base.semantic_expression(
                    argument,
                    self.local_bindings,
                    self.module_values,
                    self.parameter_positions,
                )

            context = [
                {
                    "branch": branch,
                    "expression": base.semantic_expression(
                        item,
                        self.local_bindings,
                        self.module_values,
                        self.parameter_positions,
                    ),
                }
                for branch, item in self.context_nodes
            ]
            self.contracts.add(
                json.dumps(
                    {
                        "sourcePath": self.source_path,
                        "helper": helper_name,
                        "caller": self.caller,
                        "code": code,
                        "context": context,
                        "arguments": arguments,
                    },
                    sort_keys=True,
                )
            )
        self.generic_visit(node)


base.ParameterizedCallSiteVisitor = BranchAwareParameterizedCallSiteVisitor

CHECKPOINT_COMMIT = base.CHECKPOINT_COMMIT
REPO_ROOT = base.REPO_ROOT
ParameterizedCallSiteVisitor = BranchAwareParameterizedCallSiteVisitor
parameterized_finding_parameters = base.parameterized_finding_parameters
module_bindings = base.module_bindings
function_parameter_order = base.function_parameter_order
parameterized_finding_contracts = base.parameterized_finding_contracts
published_python_paths = base.published_python_paths
candidate_python_paths = base.candidate_python_paths
git_source_at = base.git_source_at
published_contracts = base.published_contracts
candidate_contracts = base.candidate_contracts
matching_contract = base.matching_contract


class ReleaseCandidateParameterizedFindingCodeTests(
    base.ReleaseCandidateParameterizedFindingCodeTests
):
    def test_moving_call_between_if_arms_changes_branch_semantics(self):
        positive = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    license_path = root / "LICENSE"
    if license_path.is_file():
        read_text(license_path, findings, "LICENSE_ENCODING")
    else:
        findings.append("missing")
'''
        negative = positive.replace(
            '        read_text(license_path, findings, "LICENSE_ENCODING")\n    else:\n        findings.append("missing")',
            '        findings.append("present")\n    else:\n        read_text(license_path, findings, "LICENSE_ENCODING")',
        )
        expected = matching_contract(
            parameterized_finding_contracts(positive, "sample.py"),
            "LICENSE_ENCODING",
        )
        actual = matching_contract(
            parameterized_finding_contracts(negative, "sample.py"),
            "LICENSE_ENCODING",
        )
        self.assertNotEqual(expected["context"], actual["context"])

    def test_moving_call_between_match_cases_changes_branch_semantics(self):
        first_case = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(kind, root, findings):
    match kind:
        case "license":
            read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
        case "notice":
            pass
'''
        second_case = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(kind, root, findings):
    match kind:
        case "license":
            pass
        case "notice":
            read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        expected = matching_contract(
            parameterized_finding_contracts(first_case, "sample.py"),
            "LICENSE_ENCODING",
        )
        actual = matching_contract(
            parameterized_finding_contracts(second_case, "sample.py"),
            "LICENSE_ENCODING",
        )
        self.assertNotEqual(expected["context"], actual["context"])

    def test_changing_match_guard_changes_branch_semantics(self):
        positive_guard = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(kind, root, findings):
    match kind:
        case value if value == "license":
            read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        negative_guard = positive_guard.replace(
            'value == "license"',
            'value != "license"',
        )
        expected = matching_contract(
            parameterized_finding_contracts(positive_guard, "sample.py"),
            "LICENSE_ENCODING",
        )
        actual = matching_contract(
            parameterized_finding_contracts(negative_guard, "sample.py"),
            "LICENSE_ENCODING",
        )
        self.assertNotEqual(expected["context"], actual["context"])


if __name__ == "__main__":
    import unittest

    unittest.main()
