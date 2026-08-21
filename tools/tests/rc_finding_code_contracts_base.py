from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool, sha256_utf8_text_file

CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"
CHECKPOINT_PATH = REPO_ROOT / "releases" / "compatibility" / "0.10.0-finding-codes.json"
CHECKPOINT_SHA256 = "07619880db05b0065d53be54626af3246559e35e0ae895cbf60d158e42561002"


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or "git command failed")
    return completed.stdout


def git_source_at(commit: str, relative: str) -> str:
    return git_output("show", f"{commit}:{relative}")


def published_python_paths() -> list[str]:
    paths = git_output("ls-tree", "-r", "--name-only", CHECKPOINT_COMMIT, "tools").splitlines()
    return sorted(
        path
        for path in paths
        if path.endswith(".py")
        and not path.startswith("tools/tests/")
        and "/tests/" not in path
    )


def candidate_python_paths() -> list[Path]:
    return sorted(
        path
        for path in (REPO_ROOT / "tools").rglob("*.py")
        if "tests" not in path.relative_to(REPO_ROOT / "tools").parts
    )


def canonical_ast(node: ast.AST | None) -> str:
    return "" if node is None else ast.dump(node, annotate_fields=False, include_attributes=False)


def _stored_names(target: ast.AST) -> list[str]:
    return [
        item.id
        for item in ast.walk(target)
        if isinstance(item, ast.Name) and isinstance(item.ctx, (ast.Store, ast.Del))
    ]


class _BindingShapeNormalizer(ast.NodeTransformer):
    """Reduce a binding expression to a rename-independent structural shape."""

    def __init__(self, parameter_positions: dict[str, int], local_names: set[str]) -> None:
        self.parameter_positions = parameter_positions
        self.local_names = local_names

    def visit_Name(self, node: ast.Name) -> ast.AST:
        cloned = copy.deepcopy(node)
        if cloned.id in self.parameter_positions:
            cloned.id = f"_p{self.parameter_positions[cloned.id]}"
        elif cloned.id in self.local_names:
            cloned.id = "_local"
        return cloned

    def visit_arg(self, node: ast.arg) -> ast.AST:
        cloned = copy.deepcopy(node)
        if cloned.arg in self.parameter_positions:
            cloned.arg = f"_p{self.parameter_positions[cloned.arg]}"
        elif cloned.arg in self.local_names:
            cloned.arg = "_local"
        return cloned


class _FunctionScopeNameNormalizer(ast.NodeTransformer):
    """Normalize private bound identifiers without renaming module/public names."""

    def __init__(self) -> None:
        self.scopes: list[dict[str, str]] = []

    @staticmethod
    def _parameter_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        args = node.args
        names = [
            argument.arg
            for argument in (*args.posonlyargs, *args.args, *args.kwonlyargs)
        ]
        if args.vararg is not None:
            names.append(args.vararg.arg)
        if args.kwarg is not None:
            names.append(args.kwarg.arg)
        return names

    @staticmethod
    def _local_store_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
        names: set[str] = set()

        class Collector(ast.NodeVisitor):
            def visit_FunctionDef(self, item: ast.FunctionDef) -> None:
                if item is node:
                    for statement in item.body:
                        self.visit(statement)

            def visit_AsyncFunctionDef(self, item: ast.AsyncFunctionDef) -> None:
                if item is node:
                    for statement in item.body:
                        self.visit(statement)

            def visit_Lambda(self, item: ast.Lambda) -> None:
                return

            def visit_ClassDef(self, item: ast.ClassDef) -> None:
                return

            def visit_Name(self, item: ast.Name) -> None:
                if isinstance(item.ctx, (ast.Store, ast.Del)):
                    names.add(item.id)

            def visit_ExceptHandler(self, item: ast.ExceptHandler) -> None:
                if item.name:
                    names.add(item.name)
                self.generic_visit(item)

        Collector().visit(node)
        return names

    @classmethod
    def _binding_shapes(
        cls,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        parameter_positions: dict[str, int],
        local_names: set[str],
    ) -> dict[str, list[str]]:
        shapes: dict[str, list[str]] = {name: [] for name in local_names}

        def shape(prefix: str, expression: ast.AST | None) -> str:
            if expression is None:
                return prefix
            cloned = copy.deepcopy(expression)
            cloned = _BindingShapeNormalizer(parameter_positions, local_names).visit(cloned)
            ast.fix_missing_locations(cloned)
            return f"{prefix}:{canonical_ast(cloned)}"

        def add_target(target: ast.AST, prefix: str, expression: ast.AST | None) -> None:
            value = shape(prefix, expression)
            for name in _stored_names(target):
                if name in shapes:
                    shapes[name].append(value)

        class BindingCollector(ast.NodeVisitor):
            def visit_FunctionDef(self, item: ast.FunctionDef) -> None:
                if item is node:
                    for statement in item.body:
                        self.visit(statement)

            def visit_AsyncFunctionDef(self, item: ast.AsyncFunctionDef) -> None:
                if item is node:
                    for statement in item.body:
                        self.visit(statement)

            def visit_Lambda(self, item: ast.Lambda) -> None:
                return

            def visit_ClassDef(self, item: ast.ClassDef) -> None:
                return

            def visit_Assign(self, item: ast.Assign) -> None:
                for target in item.targets:
                    add_target(target, "assign", item.value)
                self.visit(item.value)

            def visit_AnnAssign(self, item: ast.AnnAssign) -> None:
                if item.value is not None:
                    add_target(item.target, "annassign", item.value)
                    self.visit(item.value)

            def visit_AugAssign(self, item: ast.AugAssign) -> None:
                add_target(item.target, f"augassign:{type(item.op).__name__}", item.value)
                self.visit(item.value)

            def visit_NamedExpr(self, item: ast.NamedExpr) -> None:
                add_target(item.target, "namedexpr", item.value)
                self.visit(item.value)

            def visit_For(self, item: ast.For) -> None:
                add_target(item.target, "for", item.iter)
                self.visit(item.iter)
                for statement in item.body:
                    self.visit(statement)
                for statement in item.orelse:
                    self.visit(statement)

            def visit_AsyncFor(self, item: ast.AsyncFor) -> None:
                add_target(item.target, "async-for", item.iter)
                self.visit(item.iter)
                for statement in item.body:
                    self.visit(statement)
                for statement in item.orelse:
                    self.visit(statement)

            def visit_comprehension(self, item: ast.comprehension) -> None:
                add_target(item.target, "comprehension", item.iter)
                self.visit(item.iter)
                for condition in item.ifs:
                    self.visit(condition)

            def visit_With(self, item: ast.With) -> None:
                for with_item in item.items:
                    if with_item.optional_vars is not None:
                        add_target(with_item.optional_vars, "with", with_item.context_expr)
                    self.visit(with_item.context_expr)
                for statement in item.body:
                    self.visit(statement)

            def visit_AsyncWith(self, item: ast.AsyncWith) -> None:
                for with_item in item.items:
                    if with_item.optional_vars is not None:
                        add_target(with_item.optional_vars, "async-with", with_item.context_expr)
                    self.visit(with_item.context_expr)
                for statement in item.body:
                    self.visit(statement)

            def visit_ExceptHandler(self, item: ast.ExceptHandler) -> None:
                if item.name and item.name in shapes:
                    shapes[item.name].append(shape("except", item.type))
                for statement in item.body:
                    self.visit(statement)

        BindingCollector().visit(node)
        return shapes

    def _mapping(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
        parameters = self._parameter_names(node)
        parameter_positions = {name: index for index, name in enumerate(parameters)}
        local_names = self._local_store_names(node) - set(parameters)
        binding_shapes = self._binding_shapes(node, parameter_positions, local_names)

        mapping = {name: f"_p{index}" for name, index in parameter_positions.items()}
        for name in local_names:
            # The first binding establishes the identity of a private local. Later
            # reassignments remain visible in dependency snapshots but must not
            # renumber or redefine the variable merely because unrelated code adds
            # another use of the same private name elsewhere in the function.
            structural_binding = (binding_shapes.get(name) or ["store"])[0]
            digest = hashlib.sha256(structural_binding.encode("utf-8")).hexdigest()[:12]
            mapping[name] = f"_v_{digest}"
        return mapping

    def _visit_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ast.FunctionDef | ast.AsyncFunctionDef:
        mapping = self._mapping(node)
        self.scopes.append(mapping)
        try:
            args = node.args
            for argument in (*args.posonlyargs, *args.args, *args.kwonlyargs):
                argument.arg = mapping.get(argument.arg, argument.arg)
            if args.vararg is not None:
                args.vararg.arg = mapping.get(args.vararg.arg, args.vararg.arg)
            if args.kwarg is not None:
                args.kwarg.arg = mapping.get(args.kwarg.arg, args.kwarg.arg)
            node.body = [self.visit(statement) for statement in node.body]
            return node
        finally:
            self.scopes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        return self._visit_function(node)

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if self.scopes:
            node.id = self.scopes[-1].get(node.id, node.id)
        return node


def normalize_bound_names(node: ast.AST) -> ast.AST:
    cloned = copy.deepcopy(node)
    normalized = _FunctionScopeNameNormalizer().visit(cloned)
    ast.fix_missing_locations(normalized)
    return normalized


class FindingMessageNormalizer(ast.NodeTransformer):
    """Remove non-contract prose from semantic dependency snapshots."""

    @staticmethod
    def _strip_docstring(node: ast.FunctionDef | ast.AsyncFunctionDef):
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            node.body = node.body[1:]
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        node = self.generic_visit(node)
        return self._strip_docstring(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        node = self.generic_visit(node)
        return self._strip_docstring(node)

    def visit_Call(self, node: ast.Call) -> ast.AST:
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "Finding":
            if len(node.args) >= 2:
                node.args[1] = ast.Constant(value="<message>")
            for keyword in node.keywords:
                if keyword.arg == "message":
                    keyword.value = ast.Constant(value="<message>")
        return node


def normalized_semantic_ast(node: ast.AST | None) -> str:
    if node is None:
        return ""
    cloned = normalize_bound_names(node)
    cloned = FindingMessageNormalizer().visit(cloned)
    ast.fix_missing_locations(cloned)
    return canonical_ast(cloned)


def loaded_names(node: ast.AST | None) -> set[str]:
    if node is None:
        return set()
    return {
        item.id
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
    }


def function_bound_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    bound = {node.name}
    arguments = node.args
    for argument in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs):
        bound.add(argument.arg)
    if arguments.vararg is not None:
        bound.add(arguments.vararg.arg)
    if arguments.kwarg is not None:
        bound.add(arguments.kwarg.arg)
    for item in ast.walk(node):
        if isinstance(item, ast.Name) and isinstance(item.ctx, (ast.Store, ast.Del)):
            bound.add(item.id)
    return bound


def dependency_names(node: ast.AST | None) -> set[str]:
    names = loaded_names(node)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        names -= function_bound_names(node)
    return names


def module_semantic_bindings(tree: ast.Module) -> dict[str, ast.AST]:
    definitions: dict[str, ast.AST] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    definitions[target.id] = statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            if statement.value is not None:
                definitions[statement.target.id] = statement.value
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions[statement.name] = statement
    return definitions


def module_function_semantic_ast(text: str, function_name: str) -> str:
    tree = ast.parse(text)
    node = module_semantic_bindings(tree).get(function_name)
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise AssertionError(f"module-level helper {function_name!r} was not found")
    return normalized_semantic_ast(node)


def finding_code(node: ast.Call) -> str | None:
    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
        return node.args[0].value
    for keyword in node.keywords:
        if (
            keyword.arg == "code"
            and isinstance(keyword.value, ast.Constant)
            and isinstance(keyword.value.value, str)
        ):
            return keyword.value.value
    return None


def finding_call_shape(node: ast.Call) -> dict[str, object]:
    positional_tail = [canonical_ast(argument) for argument in node.args[2:]]
    keywords = sorted(
        (
            keyword.arg if keyword.arg is not None else "**",
            canonical_ast(keyword.value),
        )
        for keyword in node.keywords
        if keyword.arg not in {"code", "message"}
    )
    return {
        "positionalTail": positional_tail,
        "keywords": keywords,
    }


def finding_dependency_nodes(node: ast.Call) -> list[ast.AST]:
    dependencies: list[ast.AST] = list(node.args[2:])
    dependencies.extend(
        keyword.value
        for keyword in node.keywords
        if keyword.arg not in {"code", "message"}
    )
    return dependencies


class FindingSignatureVisitor(ast.NodeVisitor):
    def __init__(self, definitions: dict[str, ast.AST], source_path: str) -> None:
        self.module_definitions = definitions
        self.source_path = source_path
        self.function = "<module>"
        self.context: list[str] = []
        self.context_nodes: list[ast.AST] = []
        self.local_bindings: dict[str, ast.AST] = {}
        self.signatures: dict[str, list[str]] = {}

    def _visit_block(self, statements: list[ast.stmt]) -> None:
        for statement in statements:
            self.visit(statement)

    def _with_context(
        self,
        marker: str,
        dependency_node: ast.AST | None,
        statements: list[ast.stmt],
    ) -> None:
        self.context.append(marker)
        if dependency_node is not None:
            self.context_nodes.append(dependency_node)
        try:
            self._visit_block(statements)
        finally:
            if dependency_node is not None:
                self.context_nodes.pop()
            self.context.pop()

    def _dependency_snapshot(self, nodes: list[ast.AST]) -> dict[str, str]:
        pending: set[str] = set()
        for node in nodes:
            pending.update(dependency_names(node))

        snapshot: dict[str, str] = {}
        visited: set[str] = set()
        while pending:
            name = pending.pop()
            if name in visited:
                continue
            visited.add(name)

            binding = self.local_bindings.get(name)
            if binding is None:
                binding = self.module_definitions.get(name)
            if binding is None:
                continue

            snapshot[name] = normalized_semantic_ast(binding)
            pending.update(dependency_names(binding) - visited)

        return dict(sorted(snapshot.items()))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        previous_function = self.function
        previous_bindings = self.local_bindings
        self.function = node.name
        self.local_bindings = {}
        try:
            self._visit_block(node.body)
        finally:
            self.function = previous_function
            self.local_bindings = previous_bindings

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        previous_function = self.function
        previous_bindings = self.local_bindings
        self.function = node.name
        self.local_bindings = {}
        try:
            self._visit_block(node.body)
        finally:
            self.function = previous_function
            self.local_bindings = previous_bindings

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.local_bindings[target.id] = node.value
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name) and node.value is not None:
            self.local_bindings[node.target.id] = node.value
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        test = canonical_ast(node.test)
        self._with_context(f"if:{test}", node.test, node.body)
        if node.orelse:
            self._with_context(f"else:{test}", node.test, node.orelse)

    def visit_For(self, node: ast.For) -> None:
        marker = f"for:{canonical_ast(node.target)} in {canonical_ast(node.iter)}"
        self._with_context(marker, node.iter, node.body)
        if node.orelse:
            self._with_context(f"for-else:{marker}", node.iter, node.orelse)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        marker = f"async-for:{canonical_ast(node.target)} in {canonical_ast(node.iter)}"
        self._with_context(marker, node.iter, node.body)
        if node.orelse:
            self._with_context(f"async-for-else:{marker}", node.iter, node.orelse)

    def visit_While(self, node: ast.While) -> None:
        test = canonical_ast(node.test)
        self._with_context(f"while:{test}", node.test, node.body)
        if node.orelse:
            self._with_context(f"while-else:{test}", node.test, node.orelse)

    def _visit_try_regions(self, node: ast.Try | ast.AST, *, star: bool) -> None:
        prefix = "try-star" if star else "try"
        handler_prefix = "except-star" if star else "except"
        self._with_context(prefix, None, node.body)
        for handler in node.handlers:
            exception_type = canonical_ast(handler.type) if handler.type is not None else "bare"
            self._with_context(
                f"{handler_prefix}:{exception_type}", handler.type, handler.body
            )
        if node.orelse:
            self._with_context(f"{prefix}-else", None, node.orelse)
        if node.finalbody:
            self._with_context(f"{prefix}-finally", None, node.finalbody)

    def visit_Try(self, node: ast.Try) -> None:
        self._visit_try_regions(node, star=False)

    if hasattr(ast, "TryStar"):
        def visit_TryStar(self, node: ast.TryStar) -> None:
            self._visit_try_regions(node, star=True)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "Finding":
            code = finding_code(node)
            if code is not None:
                dependency_nodes = list(self.context_nodes) + finding_dependency_nodes(node)
                signature = json.dumps(
                    {
                        "sourcePath": self.source_path,
                        "function": self.function,
                        "context": list(self.context),
                        "dependencies": self._dependency_snapshot(dependency_nodes),
                        "emission": finding_call_shape(node),
                    },
                    sort_keys=True,
                )
                self.signatures.setdefault(code, []).append(signature)
        self.generic_visit(node)


def finding_semantic_signatures(text: str, source_path: str = "<memory>") -> dict[str, list[str]]:
    tree = normalize_bound_names(ast.parse(text))
    visitor = FindingSignatureVisitor(module_semantic_bindings(tree), source_path)
    visitor.visit(tree)
    return {code: sorted(signatures) for code, signatures in visitor.signatures.items()}


def aggregate_signatures(sources: list[tuple[str, str]]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for source_path, text in sources:
        for code, signatures in finding_semantic_signatures(text, source_path).items():
            result.setdefault(code, set()).update(signatures)
    return result


def published_signatures() -> dict[str, set[str]]:
    return aggregate_signatures(
        [
            (relative, git_source_at(CHECKPOINT_COMMIT, relative))
            for relative in published_python_paths()
        ]
    )


def candidate_signatures() -> dict[str, set[str]]:
    return aggregate_signatures(
        [
            (path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8"))
            for path in candidate_python_paths()
        ]
    )


def project_approved_helper_changes(signature: str, code: str, contract: dict) -> str:
    payload = json.loads(signature)
    dependencies = payload.get("dependencies", {})
    for approval_id, approval in contract.get("approvedHelperSemanticChanges", {}).items():
        if code not in approval["affectedCodes"]:
            continue
        if payload.get("sourcePath") != approval["sourcePath"]:
            continue
        helper = approval["helper"]
        if helper in dependencies:
            dependencies[helper] = f"<approved-helper-semantic-change:{approval_id}>"
    return json.dumps(payload, sort_keys=True)


def finding_map(payload: dict) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for finding in payload.get("findings", []):
        result.setdefault(finding["code"], []).append(finding["message"])
    return result


class ReleaseCandidateFindingCodeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checkpoint_bytes = CHECKPOINT_PATH.read_bytes()
        cls.contract = json.loads(cls.checkpoint_bytes.decode("utf-8"))

    def test_checkpoint_is_pinned_to_published_source(self):
        self.assertEqual(sha256_utf8_text_file(CHECKPOINT_PATH), CHECKPOINT_SHA256)
        self.assertEqual(self.contract["releaseVersion"], "0.10.0")
        self.assertEqual(self.contract["tag"], "v0.10.0")
        self.assertEqual(self.contract["sourceCommit"], CHECKPOINT_COMMIT)
        self.assertEqual(self.contract["publishedSourceScope"]["root"], "tools")
        self.assertNotIn("unchangedPublishedSourceTrees", self.contract)
        self.assertIn("referenced helper implementations", self.contract["publishedSourceScope"]["comparison"])

    def test_approved_helper_semantic_changes_are_pinned_to_reviewed_source(self):
        approvals = self.contract["approvedHelperSemanticChanges"]
        self.assertEqual(set(approvals), {"tools/release/validate_release.py:read_release_state"})
        for approval_id, approval in approvals.items():
            with self.subTest(approval=approval_id):
                current_source = (REPO_ROOT / approval["sourcePath"]).read_text(encoding="utf-8")
                approved_source = git_source_at(
                    approval["approvedCandidateCommit"], approval["sourcePath"]
                )
                self.assertEqual(
                    module_function_semantic_ast(current_source, approval["helper"]),
                    module_function_semantic_ast(approved_source, approval["helper"]),
                    "approved helper changed after its reviewed compatibility source",
                )
                self.assertEqual(
                    set(approval["affectedCodes"]),
                    {"RELEASE_PUBLICATION_BLOCKED", "RELEASE_PUBLICATION_VERSION_MISMATCH"},
                )

    def test_all_published_production_finding_semantics_are_preserved(self):
        published = published_signatures()
        current = candidate_signatures()
        self.assertGreater(len(published), 20)

        approved = self.contract["approvedAdditivePublishedCodeContexts"]
        for code, expected_signatures in published.items():
            with self.subTest(code=code):
                current_signatures = current.get(code, set())
                expected_projected = {
                    project_approved_helper_changes(signature, code, self.contract)
                    for signature in expected_signatures
                }
                current_projected = {
                    project_approved_helper_changes(signature, code, self.contract)
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

    def test_new_unique_finding_codes_are_allowed(self):
        published = {"OLD_CODE": {"old-signature"}}
        current = {"OLD_CODE": {"old-signature"}, "NEW_CODE": {"new-signature"}}
        for code, signatures in published.items():
            self.assertEqual(signatures - current.get(code, set()), set())
        self.assertIn("NEW_CODE", set(current) - set(published))

    def test_semantic_signature_allows_message_rewording_but_tracks_condition_and_data(self):
        original = '''
REQUIRED_HEADINGS = ("A", "B")
def run(text):
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            Finding("PUBLIC_CODE", "Original wording.", path="sample")
'''
        reworded = '''
REQUIRED_HEADINGS = ("A", "B")
def run(text):
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            Finding("PUBLIC_CODE", "Improved human-readable wording.", path="sample")
'''
        changed_data = '''
REQUIRED_HEADINGS = ("A",)
def run(text):
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            Finding("PUBLIC_CODE", "Original wording.", path="sample")
'''
        reused = '''
REQUIRED_HEADINGS = ("A", "B")
def run(other_text):
    for heading in REQUIRED_HEADINGS:
        if heading not in other_text:
            Finding("PUBLIC_CODE", "Original wording.", path="sample")
'''
        self.assertEqual(finding_semantic_signatures(original), finding_semantic_signatures(reworded))
        self.assertNotEqual(finding_semantic_signatures(original), finding_semantic_signatures(changed_data))
        self.assertEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(reused),
            "alpha-equivalent private parameter renames must remain compatible",
        )

    def test_semantic_signature_tracks_helper_implementation_dependencies(self):
        original = '''
def normalize(value):
    """Human-readable helper documentation."""
    return value.lower()
def run(text):
    if normalize(text) == "blocked":
        Finding("PUBLIC_CODE", "Original wording.", path="sample")
'''
        documentation_only = '''
def normalize(value):
    """Improved helper documentation."""
    return value.lower()
def run(text):
    if normalize(text) == "blocked":
        Finding("PUBLIC_CODE", "Original wording.", path="sample")
'''
        changed_helper = '''
def normalize(value):
    """Human-readable helper documentation."""
    return value.upper()
def run(text):
    if normalize(text) == "blocked":
        Finding("PUBLIC_CODE", "Original wording.", path="sample")
'''
        self.assertEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(documentation_only),
        )
        self.assertNotEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(changed_helper),
        )

    def test_template_validator_emits_published_stable_path_code(self):
        with tempfile.TemporaryDirectory() as temp:
            completed = run_tool(
                "tools/validate-templates/validate_templates.py",
                "--format",
                "json",
                "--root",
                temp,
            )
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        findings = finding_map(json_result(completed))
        self.assertIn("TEMPLATE_STABLE_PATH_MISSING", findings)

    def test_generate_manifest_emits_published_warning_and_input_codes(self):
        warning = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            "--format",
            "json",
            "--name",
            "finding-code-contract",
            "--profile",
            "CLI_TOOL",
            "--language",
            "csharp",
            "--dry-run",
        )
        self.assertEqual(warning.returncode, 0, warning.stdout + warning.stderr)
        self.assertIn("MANIFEST_NO_DISCIPLINES", finding_map(json_result(warning)))

        invalid = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            "--format",
            "json",
            "--name",
            "finding-code-contract",
            "--profile",
            "NOT_A_PROFILE",
            "--language",
            "csharp",
            "--dry-run",
        )
        self.assertEqual(invalid.returncode, 2, invalid.stdout + invalid.stderr)
        self.assertIn("INPUT_ERROR", finding_map(json_result(invalid)))

    def test_release_validator_emits_published_tag_mismatch_code(self):
        completed = run_tool(
            "tools/release/validate_release.py",
            "--format",
            "json",
            "--tag",
            "v0.0.0",
        )
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("RELEASE_TAG_MISMATCH", finding_map(json_result(completed)))

    def test_representative_checkpoint_codes_are_explicit(self):
        representatives = {
            item["code"]: item["meaning"]
            for item in self.contract["representativeEmittedFindings"]
        }
        self.assertEqual(
            set(representatives),
            {
                "TEMPLATE_STABLE_PATH_MISSING",
                "MANIFEST_NO_DISCIPLINES",
                "RELEASE_TAG_MISMATCH",
                "INPUT_ERROR",
            },
        )
        self.assertTrue(all(value.strip() for value in representatives.values()))


if __name__ == "__main__":
    unittest.main()
