from __future__ import annotations

import ast
import copy
import hashlib
import json
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_generator_function_execution as generator_function_execution
import test_rc_numbered_rule_semantics as numbered_rules
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability


def _decorator_expression_contract(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[str]:
    return [literal_base.canonical_ast(item) for item in node.decorator_list]


def _decorator_dependency_snapshot(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    definitions: dict[str, ast.AST],
    module_values: dict[str, ast.AST],
) -> dict[str, str]:
    pending: set[str] = set()
    for decorator in node.decorator_list:
        pending.update(literal_base.dependency_names(decorator))

    snapshot: dict[str, str] = {}
    visited: set[str] = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)

        binding = definitions.get(name)
        if binding is None:
            binding = module_values.get(name)
        if binding is None:
            continue

        snapshot[name] = literal_base.normalized_semantic_ast(binding)
        pending.update(literal_base.dependency_names(binding) - visited)

    return dict(sorted(snapshot.items()))


def _decorator_contract(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    definitions: dict[str, ast.AST],
    module_values: dict[str, ast.AST],
) -> dict[str, object] | None:
    if not node.decorator_list:
        return None
    return {
        "expressions": _decorator_expression_contract(node),
        "dependencies": _decorator_dependency_snapshot(
            node,
            definitions,
            module_values,
        ),
    }


def _with_decorator_function_name(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    if not node.decorator_list:
        return node
    encoded = json.dumps(
        _decorator_expression_contract(node),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:12]
    cloned = copy.copy(node)
    cloned.name = f"{node.name}<decorated:{digest}>"
    return cloned


# Importing test_rc_generator_function_execution above deliberately installs the
# existing deferred-execution patches before these decorator wrappers are added.
# Literal finding semantics then include both decorator expressions and the
# transitive module-level helper/data semantics referenced by those expressions.
_original_literal_visit_function = literal_base.FindingSignatureVisitor.visit_FunctionDef
_original_literal_visit_async_function = (
    literal_base.FindingSignatureVisitor.visit_AsyncFunctionDef
)


def _literal_visit_decorated_function(self, node: ast.FunctionDef) -> None:
    if not node.decorator_list:
        _original_literal_visit_function(self, node)
        return

    expressions = _decorator_expression_contract(node)
    self.context.append(
        "decorators:" + json.dumps(expressions, sort_keys=True, separators=(",", ":"))
    )
    self.context_nodes.extend(node.decorator_list)
    try:
        _original_literal_visit_function(self, _with_decorator_function_name(node))
    finally:
        del self.context_nodes[-len(node.decorator_list) :]
        self.context.pop()


def _literal_visit_decorated_async_function(
    self, node: ast.AsyncFunctionDef
) -> None:
    if not node.decorator_list:
        _original_literal_visit_async_function(self, node)
        return

    expressions = _decorator_expression_contract(node)
    self.context.append(
        "decorators:" + json.dumps(expressions, sort_keys=True, separators=(",", ":"))
    )
    self.context_nodes.extend(node.decorator_list)
    try:
        _original_literal_visit_async_function(
            self,
            _with_decorator_function_name(node),
        )
    finally:
        del self.context_nodes[-len(node.decorator_list) :]
        self.context.pop()


literal_base.FindingSignatureVisitor.visit_FunctionDef = _literal_visit_decorated_function
literal_base.FindingSignatureVisitor.visit_AsyncFunctionDef = (
    _literal_visit_decorated_async_function
)


# Reachability inventories retain the existing control-flow implementation but
# distinguish a decorated invocation boundary from the same undecorated body.
def _patch_reachability_decorators(visitor_type) -> None:
    original_visit_function = visitor_type._visit_function

    def patched_visit_function(self, node):
        return original_visit_function(self, _with_decorator_function_name(node))

    visitor_type._visit_function = patched_visit_function


_patch_reachability_decorators(basic_reachability.ReachableFindingVisitor)
_patch_reachability_decorators(extended_reachability.ExtendedReachableFindingVisitor)


# Caller-supplied finding contracts encode caller identity and helper behavior
# separately. Decorated callers get a distinct execution identity; decorated
# emitting helpers carry the decorator expressions and referenced helper/data
# semantics in the serialized contract.
_original_parameterized_visit_function = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor._visit_function
)
_original_parameterized_visit_call = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Call
)


def _parameterized_visit_decorated_function(self, node) -> None:
    _original_parameterized_visit_function(self, _with_decorator_function_name(node))


def _parameterized_visit_decorated_call(self, node: ast.Call) -> None:
    before = set(self.contracts)
    _original_parameterized_visit_call(self, node)

    if not (
        isinstance(node.func, ast.Name)
        and node.func.id in self.parameterized_helpers
        and node.func.id in self.definitions
    ):
        return

    definition = self.definitions[node.func.id]
    decorator_contract = _decorator_contract(
        definition,
        self.definitions,
        self.module_values,
    )
    if decorator_contract is None:
        return

    added = self.contracts - before
    if not added:
        return

    self.contracts.difference_update(added)
    for raw in added:
        payload = json.loads(raw)
        if payload.get("helper") == node.func.id:
            payload["helperDecorators"] = decorator_contract
        self.contracts.add(json.dumps(payload, sort_keys=True))


parameterized_active.BranchAwareParameterizedCallSiteVisitor._visit_function = (
    _parameterized_visit_decorated_function
)
parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Call = (
    _parameterized_visit_decorated_call
)
parameterized_active.base.ParameterizedCallSiteVisitor = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor
)


class ReleaseCandidateDecoratorAndNumberedEvidenceRegressionTests(unittest.TestCase):
    def test_gov_secdev_002_expected_evidence_is_explicitly_protected(self):
        path = "governance/SECURE_DEVELOPMENT_POLICY.md"
        published_text = numbered_rules.base.git_source_at(
            numbered_rules.base.CHECKPOINT_COMMIT,
            path,
        )
        published = numbered_rules.extract_rule_field_contracts(
            published_text,
            path,
        )
        matching = [
            fields
            for contract_path, rule_id, fields in published
            if contract_path == path and rule_id == "GOV-SECDEV-002"
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(
            matching[0]["expected evidence"],
            "Configuration and tests demonstrate secure behavior.",
        )

        weakened_text = published_text.replace(
            "\n\n**Expected evidence:** Configuration and tests demonstrate secure behavior.",
            "",
            1,
        )
        findings = numbered_rules.rule_field_contract_findings(
            published,
            numbered_rules.extract_rule_field_contracts(weakened_text, path),
        )
        self.assertIn(
            f"RULE_FIELD_MISSING:{path}:GOV-SECDEV-002:expected evidence",
            findings,
        )

    def test_decorator_changes_literal_finding_semantics_and_reachability(self):
        plain = """
def gate(fn):
    return fn

def validate():
    Finding("PUBLIC_CODE", "visible", path="sample")
"""
        decorated = """
def gate(fn):
    return fn

@gate
def validate():
    Finding("PUBLIC_CODE", "visible", path="sample")
"""
        plain_signatures = literal_base.finding_semantic_signatures(plain)
        decorated_signatures = literal_base.finding_semantic_signatures(decorated)
        self.assertNotEqual(plain_signatures, decorated_signatures)

        payload = json.loads(decorated_signatures["PUBLIC_CODE"][0])
        self.assertTrue(
            any(item.startswith("decorators:") for item in payload["context"])
        )
        self.assertIn("gate", payload["dependencies"])

        self.assertNotEqual(
            extended_reachability.reachable_contracts(plain, "sample.py"),
            extended_reachability.reachable_contracts(decorated, "sample.py"),
        )

    def test_decorator_helper_behavior_changes_literal_semantics(self):
        transparent = """
def gate(fn):
    return fn

@gate
def validate():
    Finding("PUBLIC_CODE", "visible", path="sample")
"""
        suppressing = """
def gate(fn):
    def wrapped(*args, **kwargs):
        return []
    return wrapped

@gate
def validate():
    Finding("PUBLIC_CODE", "visible", path="sample")
"""
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(transparent),
            literal_base.finding_semantic_signatures(suppressing),
        )

    def test_decorated_parameterized_emitter_binds_decorator_helpers(self):
        transparent = """
def gate(fn):
    return fn

@gate
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")

def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        suppressing = """
def gate(fn):
    def wrapped(*args, **kwargs):
        return []
    return wrapped

@gate
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")

def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        transparent_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    transparent,
                    "sample.py",
                )
            )
        )
        suppressing_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    suppressing,
                    "sample.py",
                )
            )
        )
        transparent_payload = json.loads(transparent_contract)
        self.assertIn("helperDecorators", transparent_payload)
        self.assertIn(
            "gate",
            transparent_payload["helperDecorators"]["dependencies"],
        )
        self.assertNotEqual(transparent_contract, suppressing_contract)

    def test_decorated_parameterized_caller_has_distinct_execution_identity(self):
        plain = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")

def gate(fn):
    return fn

def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        decorated = plain.replace(
            "def validate(root, findings):",
            "@gate\ndef validate(root, findings):",
        )
        plain_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    plain,
                    "sample.py",
                )
            )
        )
        decorated_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    decorated,
                    "sample.py",
                )
            )
        )
        self.assertEqual(json.loads(plain_contract)["caller"], "validate")
        self.assertIn(
            "<decorated:",
            json.loads(decorated_contract)["caller"],
        )
        self.assertNotEqual(plain_contract, decorated_contract)


if __name__ == "__main__":
    unittest.main()
