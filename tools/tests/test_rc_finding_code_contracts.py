from __future__ import annotations

import ast
import copy
import hashlib
import json
import tempfile
from pathlib import Path

import rc_finding_code_contracts_base as base
import test_rc_finding_helper_runtime as finding_runtime

_MUTATING_METHODS = {
    "append",
    "extend",
    "insert",
    "remove",
    "pop",
    "clear",
    "sort",
    "reverse",
    "add",
    "discard",
    "update",
    "setdefault",
}

_BEHAVIOR_BOUND_FINDING_CONTEXTS = {
    "MANIFEST_NO_DISCIPLINES": {
        "sourcePath": "tools/generate-manifest/generate_manifest.py",
        "function": "run",
        "reason": (
            "The post-v0.10.0 secondary-profile discipline expansion intentionally changes "
            "the local dataflow feeding the published no-disciplines warning. Preserve this "
            "public code behavior with direct two-sided runtime coverage rather than freezing "
            "the implementation AST."
        ),
    },
    "RELEASE_HEAD_TAG_MISSING": {
        "sourcePath": "tools/release/validate_release.py",
        "function": "run",
        "reason": (
            "The explicit UTF-8 Git-output boundary changes the private git_output helper "
            "AST without changing the public finding contract. Preserve the public code "
            "with direct two-sided runtime coverage instead of freezing locale-dependent "
            "subprocess decoding."
        ),
    },
    **{
        code: {
            "sourcePath": "tools/validate-schemas/validate_schemas.py",
            "function": "run",
            "reason": (
                "Completion-result current-major routing intentionally expands versioned-schema "
                "validation. Direct positive and negative validator tests preserve each public "
                "code while schema and reference checks remain ordered before fixture and "
                "repository-instance validation."
            ),
        }
        for code in (
            "SCHEMA_MISSING",
            "SCHEMA_INVALID",
            "SCHEMA_ID_MISSING",
            "SCHEMA_ID_DUPLICATE",
            "SCHEMA_REMOTE_REF",
            "SCHEMA_VERSION_MISMATCH",
            "SCHEMA_POSITIVE_EXAMPLE_MISSING",
            "SCHEMA_NEGATIVE_EXAMPLE_MISSING",
        )
    },
}


class _SelfNormalizer(ast.NodeTransformer):
    def __init__(
        self,
        target: str,
        parameter_positions: dict[str, int],
        local_names: set[str],
    ) -> None:
        self.target = target
        self.parameter_positions = parameter_positions
        self.local_names = local_names

    def visit_Name(self, node: ast.Name) -> ast.AST:
        cloned = copy.deepcopy(node)
        if cloned.id == self.target:
            cloned.id = "_self"
        elif cloned.id in self.parameter_positions:
            cloned.id = f"_p{self.parameter_positions[cloned.id]}"
        elif cloned.id in self.local_names:
            cloned.id = "_local"
        return cloned

    def visit_arg(self, node: ast.arg) -> ast.AST:
        cloned = copy.deepcopy(node)
        if cloned.arg in self.parameter_positions:
            cloned.arg = f"_p{self.parameter_positions[cloned.arg]}"
        elif cloned.arg == self.target:
            cloned.arg = "_self"
        elif cloned.arg in self.local_names:
            cloned.arg = "_local"
        return cloned


def _normalized_for_local(
    node: ast.AST,
    target: str,
    parameter_positions: dict[str, int],
    local_names: set[str],
) -> str:
    cloned = copy.deepcopy(node)
    cloned = _SelfNormalizer(target, parameter_positions, local_names).visit(cloned)
    cloned = base.FindingMessageNormalizer().visit(cloned)
    ast.fix_missing_locations(cloned)
    return base.canonical_ast(cloned)


def _parent_map(node: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(node):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _branch_context(
    node: ast.AST,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[ast.AST, ast.AST],
    target: str,
    parameter_positions: dict[str, int],
    local_names: set[str],
) -> list[str]:
    markers: list[str] = []
    child = node
    while child in parents:
        parent = parents[child]
        if parent is function:
            break
        if isinstance(parent, ast.If):
            if child in parent.body:
                side = "if:true"
            elif child in parent.orelse:
                side = "if:false"
            else:
                side = "if:test"
            markers.append(
                f"{side}:{_normalized_for_local(parent.test, target, parameter_positions, local_names)}"
            )
        elif isinstance(parent, (ast.For, ast.AsyncFor)):
            if child in parent.body:
                side = "for:body"
            elif child in parent.orelse:
                side = "for:else"
            else:
                side = "for:iter"
            markers.append(
                f"{side}:{_normalized_for_local(parent.iter, target, parameter_positions, local_names)}"
            )
        elif isinstance(parent, ast.While):
            if child in parent.body:
                side = "while:body"
            elif child in parent.orelse:
                side = "while:else"
            else:
                side = "while:test"
            markers.append(
                f"{side}:{_normalized_for_local(parent.test, target, parameter_positions, local_names)}"
            )
        elif isinstance(parent, ast.Try):
            if child in parent.body:
                markers.append("try")
            elif child in parent.orelse:
                markers.append("try:else")
            elif child in parent.finalbody:
                markers.append("try:finally")
        elif isinstance(parent, ast.ExceptHandler):
            marker = (
                "except:bare"
                if parent.type is None
                else f"except:{_normalized_for_local(parent.type, target, parameter_positions, local_names)}"
            )
            markers.append(marker)
        child = parent
    markers.reverse()
    return markers


def _first_bindings(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    local_names: set[str],
) -> dict[str, ast.AST]:
    result: dict[str, ast.AST] = {}

    class Collector(ast.NodeVisitor):
        def visit_FunctionDef(self, item: ast.FunctionDef) -> None:
            if item is function:
                for statement in item.body:
                    self.visit(statement)

        def visit_AsyncFunctionDef(self, item: ast.AsyncFunctionDef) -> None:
            if item is function:
                for statement in item.body:
                    self.visit(statement)

        def visit_Lambda(self, item: ast.Lambda) -> None:
            return

        def visit_ClassDef(self, item: ast.ClassDef) -> None:
            return

        def visit_Assign(self, item: ast.Assign) -> None:
            for target in item.targets:
                for name in base._stored_names(target):
                    if name in local_names and name not in result:
                        result[name] = item.value
            self.visit(item.value)

        def visit_AnnAssign(self, item: ast.AnnAssign) -> None:
            if item.value is not None:
                for name in base._stored_names(item.target):
                    if name in local_names and name not in result:
                        result[name] = item.value
                self.visit(item.value)

        def visit_For(self, item: ast.For) -> None:
            for name in base._stored_names(item.target):
                if name in local_names and name not in result:
                    result[name] = item.iter
            self.generic_visit(item)

        def visit_AsyncFor(self, item: ast.AsyncFor) -> None:
            for name in base._stored_names(item.target):
                if name in local_names and name not in result:
                    result[name] = item.iter
            self.generic_visit(item)

    Collector().visit(function)
    return result


def _finding_dependency_roles(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    local_names: set[str],
    parameter_positions: dict[str, int],
) -> tuple[dict[str, list[str]], dict[str, int]]:
    parents = _parent_map(function)
    roles: dict[str, list[str]] = {}
    cutoffs: dict[str, int] = {}

    for node in ast.walk(function):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Finding"
            and base.finding_code(node) is not None
        ):
            continue
        dependencies = list(base.finding_dependency_nodes(node))
        child: ast.AST = node
        while child in parents:
            parent = parents[child]
            if parent is function:
                break
            if isinstance(parent, ast.If):
                dependencies.append(parent.test)
            elif isinstance(parent, (ast.For, ast.AsyncFor)):
                dependencies.append(parent.iter)
            elif isinstance(parent, ast.While):
                dependencies.append(parent.test)
            elif isinstance(parent, ast.ExceptHandler) and parent.type is not None:
                dependencies.append(parent.type)
            child = parent

        cutoff = getattr(node, "lineno", 10**9)
        for dependency in dependencies:
            names = base.loaded_names(dependency) & local_names
            for name in names:
                marker = _normalized_for_local(
                    dependency, name, parameter_positions, local_names
                )
                roles.setdefault(name, []).append(marker)
                cutoffs[name] = min(cutoffs.get(name, cutoff), cutoff)

    bindings = _first_bindings(function, local_names)
    pending = list(roles)
    while pending:
        parent_name = pending.pop()
        binding = bindings.get(parent_name)
        if binding is None:
            continue
        for dependency_name in base.loaded_names(binding) & local_names:
            if dependency_name not in roles:
                roles[dependency_name] = []
                cutoffs[dependency_name] = cutoffs[parent_name]
                pending.append(dependency_name)
            roles[dependency_name].append(
                "binding:"
                + _normalized_for_local(
                    binding,
                    dependency_name,
                    parameter_positions,
                    local_names,
                )
            )
            cutoffs[dependency_name] = min(
                cutoffs.get(dependency_name, cutoffs[parent_name]),
                cutoffs[parent_name],
            )

    return roles, cutoffs


def _mutation_target_names(target: ast.AST) -> set[str]:
    """Return locals whose container or object state is changed by a mutation target."""
    names = set(base._stored_names(target))
    for item in ast.walk(target):
        if not isinstance(item, (ast.Subscript, ast.Attribute)):
            continue
        root: ast.AST = item.value
        while isinstance(root, (ast.Subscript, ast.Attribute)):
            root = root.value
        if isinstance(root, ast.Name):
            names.add(root.id)
    return names


def _target_mutation_history(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    target: str,
    cutoff: int,
    parameter_positions: dict[str, int],
    local_names: set[str],
) -> list[str]:
    parents = _parent_map(function)
    mutations: list[tuple[int, int, str]] = []

    def add(node: ast.AST) -> None:
        line = getattr(node, "lineno", cutoff + 1)
        if line > cutoff:
            return
        context = _branch_context(
            node,
            function,
            parents,
            target,
            parameter_positions,
            local_names,
        )
        mutations.append(
            (
                line,
                getattr(node, "col_offset", 0),
                "|".join(
                    context
                    + [
                        _normalized_for_local(
                            node,
                            target,
                            parameter_positions,
                            local_names,
                        )
                    ]
                ),
            )
        )

    for node in ast.walk(function):
        if isinstance(node, ast.AugAssign) and target in _mutation_target_names(node.target):
            add(node)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(target in _mutation_target_names(item) for item in targets):
                if getattr(node, "lineno", 0) > 0:
                    add(node)
        elif isinstance(node, ast.Delete):
            if any(target in _mutation_target_names(item) for item in node.targets):
                add(node)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == target
            and node.func.attr in _MUTATING_METHODS
        ):
            add(node)

    mutations.sort()
    if mutations:
        first = mutations[0][2]
        if "Assign(" in first or "AnnAssign(" in first:
            mutations = mutations[1:]
    return [item[2] for item in mutations]


class _DependencyScopedBindingNormalizer(base._FunctionScopeNameNormalizer):
    """Give Finding-relevant locals stable mutation-scoped identities."""

    def _mapping(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
        # `read_release_state` is already pinned at the semantic AST level to the
        # independently reviewed reconciliation commit. Keep its historical local
        # projection stable so this abstraction does not double-govern the same
        # approved additive evolution.
        if node.name == "read_release_state":
            return super()._mapping(node)

        parameters = self._parameter_names(node)
        parameter_positions = {name: index for index, name in enumerate(parameters)}
        local_names = self._local_store_names(node) - set(parameters)
        binding_shapes = self._binding_shapes(node, parameter_positions, local_names)
        roles, cutoffs = _finding_dependency_roles(node, local_names, parameter_positions)

        mapping = {name: f"_p{index}" for name, index in parameter_positions.items()}
        shape_by_name: dict[str, str] = {}
        for name in local_names:
            structural_binding = (binding_shapes.get(name) or ["store"])[0]
            shape_by_name[name] = structural_binding
            digest = hashlib.sha256(structural_binding.encode("utf-8")).hexdigest()[:12]
            mapping[name] = f"_v_{digest}"

        for name, role_shapes in roles.items():
            structural_binding = shape_by_name[name]
            base_digest = hashlib.sha256(structural_binding.encode("utf-8")).hexdigest()[:12]
            mutations = _target_mutation_history(
                node,
                name,
                cutoffs[name],
                parameter_positions,
                local_names,
            )
            identity = "\n".join(
                [structural_binding, *mutations, *sorted(role_shapes)]
            )
            role_digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:10]
            mapping[name] = f"_v_{base_digest}_{role_digest}"

        return mapping


base._FunctionScopeNameNormalizer = _DependencyScopedBindingNormalizer

CHECKPOINT_COMMIT = base.CHECKPOINT_COMMIT
normalized_semantic_ast = base.normalized_semantic_ast
finding_semantic_signatures = base.finding_semantic_signatures
published_signatures = base.published_signatures


class ReleaseCandidateFindingCodeContractTests(base.ReleaseCandidateFindingCodeContractTests):
    def test_all_published_production_finding_semantics_are_preserved(self):
        published = published_signatures()
        current = base.candidate_signatures()
        self.assertGreater(len(published), 20)

        approved = self.contract["approvedAdditivePublishedCodeContexts"]
        for code, expected_signatures in published.items():
            with self.subTest(code=code):
                current_signatures = current.get(code, set())
                behavior_bound = _BEHAVIOR_BOUND_FINDING_CONTEXTS.get(code)
                if behavior_bound is not None:
                    self.assertEqual(
                        len(current_signatures),
                        1,
                        f"behavior-bound public code {code} must retain exactly one production context",
                    )
                    payload = json.loads(next(iter(current_signatures)))
                    self.assertEqual(payload["sourcePath"], behavior_bound["sourcePath"])
                    self.assertEqual(payload["function"], behavior_bound["function"])
                    continue

                expected_projected = {
                    base.project_approved_helper_changes(signature, code, self.contract)
                    for signature in expected_signatures
                }
                current_projected = {
                    base.project_approved_helper_changes(signature, code, self.contract)
                    for signature in current_signatures
                }
                self.assertEqual(
                    expected_projected - current_projected,
                    set(),
                    f"published semantic context or referenced data changed/disappeared for {code}",
                )
                additional = current_projected - expected_projected
                if code in approved:
                    self.assertEqual(len(additional), approved[code]["count"])
                    if code == "RELEASE_STATE_INVALID":
                        payloads = [json.loads(signature) for signature in additional]
                        self.assertTrue(
                            all(payload["function"] == "read_release_state" for payload in payloads)
                        )
                else:
                    self.assertEqual(
                        additional,
                        set(),
                        f"unreviewed additional semantic context reuses public code {code}",
                    )

    def test_manifest_no_disciplines_is_behavior_bound(self):
        profile_paths = [
            path
            for path in sorted((base.REPO_ROOT / "profiles").glob("*.md"))
            if path.name not in {"README.md", "MANIFEST.md"}
            and not path.name.startswith("PROFILE_")
        ]
        languages = [
            path.name
            for path in sorted((base.REPO_ROOT / "languages").iterdir())
            if path.is_dir()
        ]
        disciplines = [
            path.name
            for path in sorted((base.REPO_ROOT / "disciplines").iterdir())
            if path.is_dir()
        ]
        self.assertTrue(profile_paths and languages and disciplines)

        common_args = (
            "--format",
            "json",
            "--name",
            "rc-finding-contract",
            "--profile",
            profile_paths[0].stem,
            "--language",
            languages[0],
            "--dry-run",
        )
        no_disciplines = base.run_tool(
            "tools/generate-manifest/generate_manifest.py",
            *common_args,
        )
        self.assertEqual(
            no_disciplines.returncode,
            0,
            no_disciplines.stdout + no_disciplines.stderr,
        )
        no_disciplines_payload = base.json_result(no_disciplines)
        no_disciplines_codes = {
            finding["code"] for finding in no_disciplines_payload.get("findings", [])
        }
        self.assertIn("MANIFEST_NO_DISCIPLINES", no_disciplines_codes)

        with_discipline = base.run_tool(
            "tools/generate-manifest/generate_manifest.py",
            *common_args,
            "--discipline",
            disciplines[0],
        )
        self.assertEqual(
            with_discipline.returncode,
            0,
            with_discipline.stdout + with_discipline.stderr,
        )
        with_discipline_payload = base.json_result(with_discipline)
        with_discipline_codes = {
            finding["code"] for finding in with_discipline_payload.get("findings", [])
        }
        self.assertNotIn("MANIFEST_NO_DISCIPLINES", with_discipline_codes)

    def test_release_head_tag_missing_is_behavior_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            finding_runtime.write_release_fixture(root)

            missing = base.run_tool(
                "tools/release/validate_release.py",
                "--format",
                "json",
                "--root",
                str(root),
                "--require-head-tag",
            )
            self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
            missing_codes = {
                finding["code"]
                for finding in base.json_result(missing).get("findings", [])
            }
            self.assertIn("RELEASE_HEAD_TAG_MISSING", missing_codes)

            finding_runtime.run_git(root, "init")
            finding_runtime.run_git(root, "config", "user.email", "rc-test@example.invalid")
            finding_runtime.run_git(root, "config", "user.name", "RC Compatibility Test")
            finding_runtime.run_git(root, "add", ".")
            finding_runtime.run_git(root, "commit", "-m", "fixture")
            finding_runtime.run_git(root, "tag", "v1.0.0-rc.1")

            tagged = base.run_tool(
                "tools/release/validate_release.py",
                "--format",
                "json",
                "--root",
                str(root),
                "--require-head-tag",
            )
            self.assertEqual(tagged.returncode, 0, tagged.stdout + tagged.stderr)
            tagged_codes = {
                finding["code"]
                for finding in base.json_result(tagged).get("findings", [])
            }
            self.assertNotIn("RELEASE_HEAD_TAG_MISSING", tagged_codes)

    def test_same_shaped_locals_keep_distinct_semantic_identities(self):
        original = '''
def run(flag):
    passed = []
    failed = []
    if flag:
        passed.append("ok")
    else:
        failed.append("bad")
    if passed:
        Finding("PUBLIC_CODE", "result", path="sample")
'''
        swapped_condition = original.replace(
            "if passed:\n        Finding", "if failed:\n        Finding"
        )
        renamed = original.replace("passed", "accepted").replace("failed", "rejected")
        self.assertNotEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(swapped_condition),
        )
        self.assertEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(renamed),
        )

    def test_unrelated_unused_same_shaped_local_does_not_change_existing_identity(self):
        original = '''
def run(flag):
    passed = []
    if flag:
        passed.append("ok")
    if passed:
        Finding("PUBLIC_CODE", "result", path="sample")
'''
        with_scratch = original.replace(
            "    passed = []\n", "    scratch = []\n    passed = []\n"
        )
        self.assertEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(with_scratch),
        )

    def test_unrelated_used_same_shaped_local_does_not_change_existing_identity(self):
        original = '''
def run(flag):
    passed = []
    if flag:
        passed.append("ok")
    if passed:
        Finding("PUBLIC_CODE", "result", path="sample")
'''
        with_scratch = original.replace(
            "    passed = []\n",
            '    scratch = []\n    scratch.append("irrelevant")\n    passed = []\n',
        )
        self.assertEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(with_scratch),
        )

    def test_subscript_assignment_changes_dependency_identity(self):
        original = '''
def run(document_id):
    ids = {}
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        mutated = original.replace(
            "    if document_id in ids:\n",
            '    ids[document_id] = "path"\n    if document_id in ids:\n',
        )
        self.assertNotEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(mutated),
        )

    def test_attribute_assignment_changes_dependency_identity(self):
        original = '''
def run():
    skill = load_skill()
    if skill.name:
        Finding("SKILL_NAME_REQUIRED", "skill", path="sample")
'''
        mutated = original.replace(
            "    if skill.name:\n",
            '    skill.name = ""\n    if skill.name:\n',
        )
        self.assertNotEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(mutated),
        )

    def test_subscript_deletion_changes_dependency_identity(self):
        original = '''
def run(document_id):
    ids = {document_id: "path"}
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        mutated = original.replace(
            "    if document_id in ids:\n",
            "    del ids[document_id]\n    if document_id in ids:\n",
        )
        self.assertNotEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(mutated),
        )

    def test_attribute_deletion_changes_dependency_identity(self):
        original = '''
def run():
    skill = load_skill()
    if skill.name:
        Finding("SKILL_NAME_REQUIRED", "skill", path="sample")
'''
        mutated = original.replace(
            "    if skill.name:\n",
            "    del skill.name\n    if skill.name:\n",
        )
        self.assertNotEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(mutated),
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
