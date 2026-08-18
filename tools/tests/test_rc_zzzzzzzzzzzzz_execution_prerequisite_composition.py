from __future__ import annotations

import ast
import copy
import hashlib
import json
import operator
import unittest
from collections import Counter
from functools import lru_cache
from typing import Any

import rc_finding_code_contracts_base as literal_base
import rc_reachability_semantics as reachability_semantics
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzzzzzzzzzz_execution_prerequisites as prerequisite_execution  # noqa: F401


# Compose the try-prerequisite remediation without changing the stable context
# labels that earlier permanent regressions intentionally protect.


def _handler_is_catch_all(handler: ast.ExceptHandler) -> bool:
    node = handler.type
    if node is None:
        return True
    if isinstance(node, ast.Name):
        return node.id in {"Exception", "BaseException"}
    if isinstance(node, ast.Tuple):
        return any(
            isinstance(item, ast.Name)
            and item.id in {"Exception", "BaseException"}
            for item in node.elts
        )
    return False


def _handler_prerequisite_node(node: ast.AST, handler_index: int) -> ast.Module:
    statements: list[ast.stmt] = list(copy.deepcopy(getattr(node, "body")))
    handlers = list(getattr(node, "handlers"))
    for index, previous in enumerate(handlers[:handler_index]):
        type_node = (
            copy.deepcopy(previous.type)
            if previous.type is not None
            else ast.Constant(value="<bare-except>")
        )
        statements.append(
            ast.Expr(
                value=ast.Tuple(
                    elts=[
                        ast.Constant(value=f"prior-handler:{index}"),
                        type_node,
                    ],
                    ctx=ast.Load(),
                )
            )
        )
        statements.extend(copy.deepcopy(previous.body))
    module = ast.Module(body=statements, type_ignores=[])
    ast.fix_missing_locations(module)
    return module


_MISSING = object()


def _visit_literal_handler(
    visitor,
    marker: str,
    prerequisite: ast.Module,
    statements: list[ast.stmt],
) -> None:
    # Keep the pre-existing exception-region marker stable, but inject the try
    # prerequisite into the dependency closure so try-body/helper drift and
    # earlier-handler ordering remain semantic changes.
    key = "__handler_prerequisite_" + hashlib.sha256(
        literal_base.normalized_semantic_ast(prerequisite).encode("utf-8")
    ).hexdigest()[:16]
    previous = visitor.local_bindings.get(key, _MISSING)
    visitor.local_bindings[key] = prerequisite
    visitor.context.append(marker)
    visitor.context_nodes.append(ast.Name(id=key, ctx=ast.Load()))
    try:
        for statement in statements:
            visitor.visit(statement)
    finally:
        visitor.context_nodes.pop()
        visitor.context.pop()
        if previous is _MISSING:
            visitor.local_bindings.pop(key, None)
        else:
            visitor.local_bindings[key] = previous


def _literal_visit_try_regions(self, node: ast.AST, *, star: bool) -> None:
    prefix = "try-star" if star else "try"
    handler_prefix = "except-star" if star else "except"

    self._with_context(prefix, None, getattr(node, "body"))
    for index, handler in enumerate(getattr(node, "handlers")):
        exception_type = (
            literal_base.canonical_ast(handler.type)
            if handler.type is not None
            else "bare"
        )
        _visit_literal_handler(
            self,
            f"{handler_prefix}:{exception_type}",
            _handler_prerequisite_node(node, index),
            handler.body,
        )
        if _handler_is_catch_all(handler):
            break

    orelse = getattr(node, "orelse")
    finalbody = getattr(node, "finalbody")
    if orelse:
        self._with_context(f"{prefix}-else", None, orelse)
    if finalbody:
        self._with_context(f"{prefix}-finally", None, finalbody)


literal_base.FindingSignatureVisitor._visit_try_regions = _literal_visit_try_regions


def _parameterized_prerequisite_expression(
    visitor,
    node: ast.AST,
    handler_index: int,
    handler: ast.ExceptHandler,
) -> ast.Tuple:
    prerequisite = _handler_prerequisite_node(node, handler_index)
    prerequisite_text = parameterized_active.base.semantic_expression(
        prerequisite,
        visitor.local_bindings,
        visitor.module_values,
        visitor.parameter_positions,
    )

    helper_semantics: list[str] = []
    called_names = {
        call.func.id
        for call in ast.walk(prerequisite)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
    }
    for name in sorted(called_names):
        definition = visitor.definitions.get(name)
        if definition is not None:
            helper_semantics.append(
                literal_base.normalized_semantic_ast(definition)
            )

    handler_type = (
        copy.deepcopy(handler.type)
        if handler.type is not None
        else ast.Constant(value=None)
    )
    return ast.Tuple(
        elts=[
            handler_type,
            ast.Constant(
                value="\n".join(
                    [prerequisite_text, *helper_semantics]
                )
            ),
        ],
        ctx=ast.Load(),
    )


def _parameterized_visit_try_regions(
    self,
    node: ast.AST,
    prefix: str = "try",
) -> None:
    self._with_context(
        f"{prefix}:body",
        ast.Constant(value=prefix),
        getattr(node, "body"),
    )
    for index, handler in enumerate(getattr(node, "handlers")):
        self._with_context(
            f"{prefix}:except:{index}",
            _parameterized_prerequisite_expression(
                self, node, index, handler
            ),
            handler.body,
        )
        if _handler_is_catch_all(handler):
            break

    orelse = getattr(node, "orelse")
    finalbody = getattr(node, "finalbody")
    if orelse:
        self._with_context(
            f"{prefix}:else",
            ast.Constant(value=prefix),
            orelse,
        )
    if finalbody:
        self._with_context(
            f"{prefix}:finally",
            ast.Constant(value=prefix),
            finalbody,
        )


parameterized_active.BranchAwareParameterizedCallSiteVisitor._visit_try_regions = (
    _parameterized_visit_try_regions
)
parameterized_active.base.ParameterizedCallSiteVisitor = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor
)


def _visit_try_reachability(self, node: ast.AST) -> None:
    self._visit_block(getattr(node, "body"))
    for handler in getattr(node, "handlers"):
        if handler.type is not None:
            self.visit(handler.type)
        self._visit_block(handler.body)
        if _handler_is_catch_all(handler):
            break
    self._visit_block(getattr(node, "orelse"))
    self._visit_block(getattr(node, "finalbody"))


for _visitor_type in (
    basic_reachability.ReachableFindingVisitor,
    extended_reachability.ExtendedReachableFindingVisitor,
):
    _visitor_type.visit_Try = _visit_try_reachability
    if hasattr(ast, "TryStar"):
        _visitor_type.visit_TryStar = _visit_try_reachability


def _visit_parameterized_try(self, node: ast.Try) -> None:
    _parameterized_visit_try_regions(self, node, "try")


def _visit_parameterized_try_star(self, node: ast.AST) -> None:
    _parameterized_visit_try_regions(self, node, "try*")


parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_Try = (
    _visit_parameterized_try
)
if hasattr(ast, "TryStar"):
    parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_TryStar = (
        _visit_parameterized_try_star
    )


# The current validate-all runner intentionally wraps the unit-test path in the
# compatibility_history context manager. That post-v0.10 wrapper has already
# been reviewed for shallow/archive operation. The execution-aware scanner now
# correctly sees it as a prerequisite, so project only that exact approved
# wrapper when comparing historical v0.10 finding semantics. The wrapper shape
# is validated here first; unrelated with-statements are never projected.


_RUN_ALL = literal_base.REPO_ROOT / "tools/validate-all/run_all.py"


@lru_cache(maxsize=1)
def _approved_run_all_history_wrapper() -> bool:
    tree = ast.parse(_RUN_ALL.read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    helper = functions.get("compatibility_history")
    run = functions.get("run")
    if helper is None or run is None:
        return False

    decorators = {
        node.id
        for node in helper.decorator_list
        if isinstance(node, ast.Name)
    }
    if "contextmanager" not in decorators:
        return False

    helper_names = {
        node.id for node in ast.walk(helper) if isinstance(node, ast.Name)
    }
    required_helper_names = {
        "_required_history_missing",
        "COMPATIBILITY_HISTORY_BUNDLE",
        "_populate_temporary_history",
        "_write_history_git_wrapper",
        "_HISTORY_REAL_GIT",
        "_HISTORY_SOURCE_ROOT",
        "_HISTORY_GIT_DIR",
        "_HISTORY_SELECTORS",
    }
    if not required_helper_names.issubset(helper_names):
        return False
    if not any(isinstance(node, ast.Yield) for node in ast.walk(helper)):
        return False
    if not any(
        isinstance(node, ast.Try) and node.finalbody
        for node in ast.walk(helper)
    ):
        return False

    history_assignment = next(
        (
            statement
            for statement in run.body
            if isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and statement.targets[0].id == "history"
        ),
        None,
    )
    if history_assignment is None or not isinstance(
        history_assignment.value, ast.IfExp
    ):
        return False

    value = history_assignment.value
    if not (
        isinstance(value.test, ast.Attribute)
        and isinstance(value.test.value, ast.Name)
        and value.test.value.id == "args"
        and value.test.attr == "include_tests"
        and isinstance(value.body, ast.Call)
        and isinstance(value.body.func, ast.Name)
        and value.body.func.id == "compatibility_history"
        and len(value.body.args) == 1
        and isinstance(value.body.args[0], ast.Name)
        and value.body.args[0].id == "root"
        and isinstance(value.orelse, ast.Call)
        and isinstance(value.orelse.func, ast.Name)
        and value.orelse.func.id == "nullcontext"
        and not value.orelse.args
    ):
        return False

    wrapper = next(
        (
            statement
            for statement in run.body
            if isinstance(statement, ast.With)
        ),
        None,
    )
    return bool(
        wrapper
        and len(wrapper.items) == 1
        and isinstance(wrapper.items[0].context_expr, ast.Name)
        and wrapper.items[0].context_expr.id == "history"
        and wrapper.items[0].optional_vars is None
    )


_previous_projection = literal_base.project_approved_helper_changes


@lru_cache(maxsize=None)
def _published_run_all_signatures(code: str) -> tuple[str, ...]:
    source_path = "tools/validate-all/run_all.py"
    text = literal_base.git_source_at(
        literal_base.CHECKPOINT_COMMIT,
        source_path,
    )
    return tuple(
        literal_base.finding_semantic_signatures(
            text,
            source_path,
        ).get(code, [])
    )


def _same_non_wrapper_contract(candidate: dict, published: dict) -> bool:
    keys = ("sourcePath", "function", "context", "emission", "sink")
    return all(candidate.get(key) == published.get(key) for key in keys)


def _project_approved_execution_prerequisites(
    signature: str,
    code: str,
    contract: dict,
) -> str:
    projected = _previous_projection(signature, code, contract)
    payload = json.loads(projected)
    if (
        payload.get("sourcePath") != "tools/validate-all/run_all.py"
        or not _approved_run_all_history_wrapper()
    ):
        return projected

    context = payload.get("context", [])
    stripped_context = [
        marker
        for marker in context
        if not marker.startswith("with:body:requires-entry:")
    ]
    if stripped_context == context:
        return projected

    candidate = copy.deepcopy(payload)
    candidate["context"] = stripped_context
    candidate_dependencies = candidate.get("dependencies", {})

    for published_signature in _published_run_all_signatures(code):
        expected = json.loads(
            _previous_projection(published_signature, code, contract)
        )
        if not _same_non_wrapper_contract(candidate, expected):
            continue
        expected_dependencies = expected.get("dependencies", {})
        if all(
            candidate_dependencies.get(name) == value
            for name, value in expected_dependencies.items()
        ):
            candidate["dependencies"] = expected_dependencies
            return json.dumps(candidate, sort_keys=True)

    # No historical contract matched, so preserve the stronger candidate
    # signature and let the compatibility assertion fail.
    return projected


literal_base.project_approved_helper_changes = (
    _project_approved_execution_prerequisites
)


# Keep the prior overlay's focused test aligned with the stable handler marker:
# prerequisite identity belongs in dependencies, not in the region label.


def _test_try_handler_signature_tracks_try_body_helper_semantics(self) -> None:
    raising = """
def load_json(path):
    raise ValueError("invalid")
def validate(path):
    try:
        load_json(path)
    except ValueError:
        Finding("PUBLIC_CODE", "invalid")
"""
    non_raising = """
def load_json(path):
    return {}
def validate(path):
    try:
        load_json(path)
    except ValueError:
        Finding("PUBLIC_CODE", "invalid")
"""
    expected = literal_base.finding_semantic_signatures(raising)
    actual = literal_base.finding_semantic_signatures(non_raising)
    self.assertNotEqual(expected, actual)
    payload = json.loads(expected["PUBLIC_CODE"][0])
    self.assertEqual(
        payload["context"],
        ["except:Name('ValueError', Load())"],
    )
    self.assertIn("load_json", payload["dependencies"])
    self.assertTrue(
        any(
            name.startswith("__handler_prerequisite_")
            for name in payload["dependencies"]
        )
    )


prerequisite_execution.ReleaseCandidateExecutionPrerequisiteRegressionTests.test_try_handler_signature_tracks_try_body_helper_semantics = (
    _test_try_handler_signature_tracks_try_body_helper_semantics
)


class ReleaseCandidateExecutionPrerequisiteCompositionTests(unittest.TestCase):
    def test_run_all_history_wrapper_is_the_approved_projection_shape(self) -> None:
        self.assertTrue(_approved_run_all_history_wrapper())

    @unittest.skipUnless(
        hasattr(ast, "TryStar"),
        "requires Python exception groups",
    )
    def test_try_star_handler_keeps_stable_region_label_and_adds_prerequisite_dependency(
        self,
    ) -> None:
        source = """
def validate():
    try:
        parse()
    except* ValueError:
        Finding("PUBLIC_CODE", "invalid")
"""
        payload = json.loads(
            literal_base.finding_semantic_signatures(source)["PUBLIC_CODE"][0]
        )
        self.assertEqual(
            payload["context"],
            ["except-star:Name('ValueError', Load())"],
        )
        self.assertTrue(
            any(
                name.startswith("__handler_prerequisite_")
                for name in payload["dependencies"]
            )
        )

    def test_earlier_broad_handler_hides_later_parameterized_call(self) -> None:
        source = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(path, findings):
    try:
        int(path)
    except Exception:
        pass
    except ValueError:
        read_text(path, findings, "PUBLIC_CODE")
"""
        self.assertEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                source, "sample.py"
            ),
            set(),
        )


if __name__ == "__main__":
    unittest.main()
