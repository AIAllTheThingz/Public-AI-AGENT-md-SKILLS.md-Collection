from __future__ import annotations

import ast
import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as literal_base
import rc_parameterized_finding_codes_base as parameterized_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_helper_mutations as helper_mutations
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability


def _visit_lambda_defaults(visitor: ast.NodeVisitor, node: ast.Lambda) -> None:
    for default in node.args.defaults:
        visitor.visit(default)
    for default in node.args.kw_defaults:
        if default is not None:
            visitor.visit(default)


def _lambda_binding_for_call(visitor, node: ast.Call) -> ast.Lambda | None:
    if isinstance(node.func, ast.Lambda):
        return node.func
    if not isinstance(node.func, ast.Name):
        return None
    for attribute in ("local_bindings", "module_definitions", "module_values"):
        bindings = getattr(visitor, attribute, {})
        binding = bindings.get(node.func.id)
        if isinstance(binding, ast.Lambda):
            return binding
    return None


def _lambda_argument_bindings(node: ast.Lambda, call: ast.Call) -> dict[str, ast.AST]:
    positional = [*node.args.posonlyargs, *node.args.args]
    result: dict[str, ast.AST] = {}
    for index, argument in enumerate(call.args):
        if index < len(positional) and not isinstance(argument, ast.Starred):
            result[positional[index].arg] = argument
    for keyword in call.keywords:
        if keyword.arg is None:
            continue
        for argument in [*positional, *node.args.kwonlyargs]:
            if argument.arg == keyword.arg:
                result[argument.arg] = keyword.value
                break
    if node.args.defaults:
        first_default = len(positional) - len(node.args.defaults)
        for index, default in enumerate(node.args.defaults, start=first_default):
            result.setdefault(positional[index].arg, default)
    for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        if default is not None:
            result.setdefault(argument.arg, default)
    return result


_original_literal_visit_call = literal_base.FindingSignatureVisitor.visit_Call


def _literal_visit_lambda(self, node: ast.Lambda) -> None:
    _visit_lambda_defaults(self, node)


def _literal_visit_call(self, node: ast.Call) -> None:
    deferred = _lambda_binding_for_call(self, node)
    if deferred is None:
        _original_literal_visit_call(self, node)
        return

    if isinstance(node.func, ast.Lambda):
        self.visit(node.func)
    for argument in node.args:
        self.visit(argument)
    for keyword in node.keywords:
        self.visit(keyword.value)

    active = getattr(self, "_active_lambda_bodies", set())
    marker = id(deferred)
    if marker in active:
        return
    previous_active = active
    previous_function = self.function
    previous_bindings = self.local_bindings
    self._active_lambda_bodies = set(active) | {marker}
    self.function = f"{previous_function}.<lambda>"
    self.local_bindings = dict(previous_bindings)
    self.local_bindings.update(_lambda_argument_bindings(deferred, node))
    self.context.append("lambda:invoked")
    try:
        self.visit(deferred.body)
    finally:
        self.context.pop()
        self.local_bindings = previous_bindings
        self.function = previous_function
        self._active_lambda_bodies = previous_active


literal_base.FindingSignatureVisitor.visit_Lambda = _literal_visit_lambda
literal_base.FindingSignatureVisitor.visit_Call = _literal_visit_call


def _patch_reachability_visitor(visitor_type) -> None:
    original_init = visitor_type.__init__
    original_visit_call = visitor_type.visit_Call
    original_visit_function = visitor_type._visit_function

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._deferred_lambdas: dict[str, ast.Lambda] = {}
        self._active_lambda_bodies: set[int] = set()

    def visit_lambda(self, node: ast.Lambda) -> None:
        _visit_lambda_defaults(self, node)

    def visit_assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        for target in node.targets:
            if isinstance(target, ast.Name):
                if isinstance(node.value, ast.Lambda):
                    self._deferred_lambdas[target.id] = node.value
                else:
                    self._deferred_lambdas.pop(target.id, None)
            else:
                self.visit(target)

    def visit_annassign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)
        if isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.Lambda):
                self._deferred_lambdas[node.target.id] = node.value
            else:
                self._deferred_lambdas.pop(node.target.id, None)
        else:
            self.visit(node.target)

    def patched_visit_function(self, node):
        previous = self._deferred_lambdas
        self._deferred_lambdas = dict(previous)
        try:
            original_visit_function(self, node)
        finally:
            self._deferred_lambdas = previous

    def patched_visit_call(self, node: ast.Call) -> None:
        deferred = None
        if isinstance(node.func, ast.Lambda):
            deferred = node.func
        elif isinstance(node.func, ast.Name):
            deferred = self._deferred_lambdas.get(node.func.id)
        if deferred is None:
            original_visit_call(self, node)
            return
        if isinstance(node.func, ast.Lambda):
            self.visit(node.func)
        for argument in node.args:
            self.visit(argument)
        for keyword in node.keywords:
            self.visit(keyword.value)
        marker = id(deferred)
        if marker in self._active_lambda_bodies:
            return
        self._active_lambda_bodies.add(marker)
        try:
            self.visit(deferred.body)
        finally:
            self._active_lambda_bodies.remove(marker)

    visitor_type.__init__ = patched_init
    visitor_type.visit_Lambda = visit_lambda
    visitor_type.visit_Assign = visit_assign
    visitor_type.visit_AnnAssign = visit_annassign
    visitor_type._visit_function = patched_visit_function
    visitor_type.visit_Call = patched_visit_call


_patch_reachability_visitor(basic_reachability.ReachableFindingVisitor)
_patch_reachability_visitor(extended_reachability.ExtendedReachableFindingVisitor)


def _execution_aware_parameterized_finding_parameters(
    tree: ast.Module,
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for statement in tree.body:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        parameters = set(parameterized_base.function_parameter_order(statement)) | {
            argument.arg for argument in statement.args.kwonlyargs
        }
        used: set[str] = set()

        class Visitor(ast.NodeVisitor):
            def __init__(self) -> None:
                self.lambdas: dict[str, ast.Lambda] = {}
                self.active: set[int] = set()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                return

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                return

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                return

            def visit_Lambda(self, node: ast.Lambda) -> None:
                _visit_lambda_defaults(self, node)

            def visit_Assign(self, node: ast.Assign) -> None:
                self.visit(node.value)
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if isinstance(node.value, ast.Lambda):
                            self.lambdas[target.id] = node.value
                        else:
                            self.lambdas.pop(target.id, None)

            def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
                if node.value is not None:
                    self.visit(node.value)
                if isinstance(node.target, ast.Name):
                    if isinstance(node.value, ast.Lambda):
                        self.lambdas[node.target.id] = node.value
                    else:
                        self.lambdas.pop(node.target.id, None)

            def visit_Call(self, node: ast.Call) -> None:
                if isinstance(node.func, ast.Name) and node.func.id == "Finding":
                    expression = parameterized_base.finding_code_expression(node)
                    if isinstance(expression, ast.Name) and expression.id in parameters:
                        used.add(expression.id)
                deferred = None
                if isinstance(node.func, ast.Lambda):
                    deferred = node.func
                elif isinstance(node.func, ast.Name):
                    deferred = self.lambdas.get(node.func.id)
                if deferred is not None:
                    if isinstance(node.func, ast.Lambda):
                        self.visit(node.func)
                    for argument in node.args:
                        self.visit(argument)
                    for keyword in node.keywords:
                        self.visit(keyword.value)
                    marker = id(deferred)
                    if marker not in self.active:
                        self.active.add(marker)
                        try:
                            self.visit(deferred.body)
                        finally:
                            self.active.remove(marker)
                    return
                self.generic_visit(node)

        visitor = Visitor()
        for body_statement in statement.body:
            visitor.visit(body_statement)
        if used:
            result[statement.name] = used
    return result


parameterized_base.parameterized_finding_parameters = (
    _execution_aware_parameterized_finding_parameters
)
parameterized_active.base.parameterized_finding_parameters = (
    _execution_aware_parameterized_finding_parameters
)
parameterized_active.parameterized_finding_parameters = (
    _execution_aware_parameterized_finding_parameters
)


_original_parameterized_visit_call = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Call
)


def _parameterized_visit_lambda(self, node: ast.Lambda) -> None:
    _visit_lambda_defaults(self, node)


def _parameterized_visit_call(self, node: ast.Call) -> None:
    deferred = _lambda_binding_for_call(self, node)
    if deferred is None:
        _original_parameterized_visit_call(self, node)
        return
    if isinstance(node.func, ast.Lambda):
        self.visit(node.func)
    for argument in node.args:
        self.visit(argument)
    for keyword in node.keywords:
        self.visit(keyword.value)
    active = getattr(self, "_active_lambda_bodies", set())
    marker = id(deferred)
    if marker in active:
        return
    previous_active = active
    previous_bindings = self.local_bindings
    self._active_lambda_bodies = set(active) | {marker}
    self.local_bindings = dict(previous_bindings)
    self.local_bindings.update(_lambda_argument_bindings(deferred, node))
    self.context_nodes.append(("lambda:invoked", ast.Constant(value="lambda")))
    try:
        self.visit(deferred.body)
    finally:
        self.context_nodes.pop()
        self.local_bindings = previous_bindings
        self._active_lambda_bodies = previous_active


parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Lambda = (
    _parameterized_visit_lambda
)
parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Call = (
    _parameterized_visit_call
)


_original_published_helper_mutations = helper_mutations.published_helper_mutation_contracts
_original_candidate_helper_mutations = helper_mutations.candidate_helper_mutation_contracts


def _helper_semantics_from_source(text: str, helper_name: str) -> str | None:
    tree = ast.parse(text)
    for statement in tree.body:
        if (
            isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
            and statement.name == helper_name
        ):
            return helper_mutations._helper_semantics(statement)
    return None


def _project_approved_helper_mutations(contracts: set[str]) -> set[str]:
    checkpoint = json.loads(
        literal_base.CHECKPOINT_PATH.read_text(encoding="utf-8")
    )
    approvals = checkpoint.get("approvedHelperSemanticChanges", {})
    if not approvals:
        return contracts

    semantic_pairs = []
    for approval_id, approval in approvals.items():
        source_path = approval["sourcePath"]
        helper_name = approval["helper"]
        published_source = literal_base.git_source_at(
            literal_base.CHECKPOINT_COMMIT, source_path
        )
        approved_source = literal_base.git_source_at(
            approval["approvedCandidateCommit"], source_path
        )
        current_source = (literal_base.REPO_ROOT / source_path).read_text(
            encoding="utf-8"
        )
        published_semantics = _helper_semantics_from_source(
            published_source, helper_name
        )
        approved_semantics = _helper_semantics_from_source(
            approved_source, helper_name
        )
        current_semantics = _helper_semantics_from_source(
            current_source, helper_name
        )
        semantic_pairs.append(
            (
                source_path,
                published_semantics,
                approved_semantics,
                current_semantics == approved_semantics,
                approval_id,
            )
        )

    projected: set[str] = set()
    for raw in contracts:
        payload = json.loads(raw)
        for (
            source_path,
            published_semantics,
            approved_semantics,
            current_is_pinned,
            approval_id,
        ) in semantic_pairs:
            if payload.get("sourcePath") != source_path or not current_is_pinned:
                continue
            if payload.get("helperSemantics") in {
                published_semantics,
                approved_semantics,
            }:
                payload["helperSemantics"] = (
                    f"<approved-helper-semantic-change:{approval_id}>"
                )
                break
        projected.add(json.dumps(payload, sort_keys=True))
    return projected


def _published_helper_mutations_with_projection() -> set[str]:
    return _project_approved_helper_mutations(
        _original_published_helper_mutations()
    )


def _candidate_helper_mutations_with_projection() -> set[str]:
    return _project_approved_helper_mutations(
        _original_candidate_helper_mutations()
    )


helper_mutations.published_helper_mutation_contracts = (
    _published_helper_mutations_with_projection
)
helper_mutations.candidate_helper_mutation_contracts = (
    _candidate_helper_mutations_with_projection
)


class ReleaseCandidateDeferredExecutionTests(unittest.TestCase):
    def test_discarded_literal_finding_lambda_is_not_a_semantic_emission(self):
        direct = """
def validate():
    Finding("PUBLIC_CODE", "visible", path="sample")
"""
        discarded = """
def validate():
    deferred = lambda: Finding("PUBLIC_CODE", "hidden", path="sample")
"""
        invoked = """
def validate():
    deferred = lambda: Finding("PUBLIC_CODE", "visible", path="sample")
    deferred()
"""
        self.assertIn(
            "PUBLIC_CODE", literal_base.finding_semantic_signatures(direct)
        )
        self.assertNotIn(
            "PUBLIC_CODE", literal_base.finding_semantic_signatures(discarded)
        )
        self.assertIn(
            "PUBLIC_CODE", literal_base.finding_semantic_signatures(invoked)
        )

    def test_discarded_literal_lambda_is_not_reachable(self):
        discarded = """
def validate():
    deferred = lambda: Finding("PUBLIC_CODE", "hidden")
"""
        invoked = """
def validate():
    deferred = lambda: Finding("PUBLIC_CODE", "visible")
    deferred()
"""
        self.assertEqual(
            extended_reachability.reachable_contracts(
                discarded, "sample.py"
            ),
            Counter(),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(
                invoked, "sample.py"
            )[("sample.py", "validate", "PUBLIC_CODE")],
            1,
        )

    def test_parameterized_helper_discovery_ignores_discarded_lambda(self):
        discarded = """
def emit(code):
    deferred = lambda: Finding(code, "hidden")
"""
        invoked = """
def emit(code):
    deferred = lambda: Finding(code, "visible")
    deferred()
"""
        self.assertEqual(
            _execution_aware_parameterized_finding_parameters(
                ast.parse(discarded)
            ),
            {},
        )
        self.assertEqual(
            _execution_aware_parameterized_finding_parameters(
                ast.parse(invoked)
            ),
            {"emit": {"code"}},
        )

    def test_parameterized_call_site_requires_lambda_invocation(self):
        discarded = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    deferred = lambda: read_text(
        root / "LICENSE", findings, "LICENSE_ENCODING"
    )
"""
        invoked = discarded + "    deferred()\n"
        self.assertEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                discarded, "sample.py"
            ),
            set(),
        )
        contracts = parameterized_reachability.reachable_parameterized_contracts(
            invoked, "sample.py"
        )
        self.assertEqual(len(contracts), 1)
        payload = json.loads(next(iter(contracts)))
        self.assertEqual(payload["code"], "LICENSE_ENCODING")

    def test_approved_helper_projection_keeps_future_drift_pinned(self):
        checkpoint = json.loads(
            literal_base.CHECKPOINT_PATH.read_text(encoding="utf-8")
        )
        approval = checkpoint["approvedHelperSemanticChanges"][
            "tools/release/validate_release.py:read_release_state"
        ]
        approved_source = literal_base.git_source_at(
            approval["approvedCandidateCommit"], approval["sourcePath"]
        )
        current_source = (
            literal_base.REPO_ROOT / approval["sourcePath"]
        ).read_text(encoding="utf-8")
        self.assertEqual(
            literal_base.module_function_semantic_ast(
                current_source, approval["helper"]
            ),
            literal_base.module_function_semantic_ast(
                approved_source, approval["helper"]
            ),
            "approved helper drifted beyond its reviewed reconciliation source",
        )


if __name__ == "__main__":
    unittest.main()
