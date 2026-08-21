from __future__ import annotations

import ast
import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as literal_base
import test_rc_generator_function_execution as generator_execution
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution


_DESTRUCTIVE_SINK_METHODS = {
    "clear",
    "pop",
    "remove",
    "discard",
    "sort",
    "reverse",
    "__setitem__",
    "__delitem__",
}


def _root_name(node: ast.AST) -> str | None:
    current = node
    while isinstance(current, (ast.Attribute, ast.Subscript)):
        current = current.value
    return current.id if isinstance(current, ast.Name) else None


def _expression_path(node: ast.AST) -> tuple[str, ...] | None:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        base = _expression_path(node.value)
        return None if base is None else (*base, f".{node.attr}")
    if isinstance(node, ast.Subscript):
        base = _expression_path(node.value)
        return (
            None
            if base is None
            else (*base, f"[{literal_base.canonical_ast(node.slice)}]")
        )
    return None


def _enclosing_function(
    node: ast.AST,
    parents: dict[int, ast.AST],
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    current = node
    while True:
        parent = parents.get(id(current))
        if parent is None:
            return None
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return parent
        if isinstance(parent, (ast.Lambda, ast.ClassDef)):
            return None
        current = parent


def _belongs_to_function(
    node: ast.AST,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[int, ast.AST],
) -> bool:
    current = node
    while True:
        parent = parents.get(id(current))
        if parent is None:
            return False
        if parent is function:
            return True
        if isinstance(
            parent,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
        ):
            return False
        current = parent


def _finding_sink_receiver(
    node: ast.Call,
    parents: dict[int, ast.AST],
) -> ast.AST | None:
    """Return the receiver whose method ultimately consumes this Finding value."""

    current: ast.AST = node
    while True:
        parent = parents.get(id(current))
        if parent is None:
            return None

        if isinstance(parent, ast.Call):
            positional = sink_execution._index_identity(parent.args, current)
            keyword = any(item.value is current for item in parent.keywords)
            if positional is not None or keyword:
                if isinstance(parent.func, ast.Attribute):
                    return parent.func.value
                return None
            if parent.func is current:
                return None

        if isinstance(
            parent,
            (
                ast.List,
                ast.Tuple,
                ast.Set,
                ast.Dict,
                ast.Starred,
                ast.keyword,
                ast.Await,
                ast.IfExp,
                ast.BoolOp,
            ),
        ):
            current = parent
            continue

        return None


def _sink_state_context(
    node: ast.AST,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[int, ast.AST],
) -> list[str]:
    markers: list[str] = []
    current = node
    try_star = getattr(ast, "TryStar", ())
    while True:
        parent = parents.get(id(current))
        if parent is None or parent is function:
            break
        if isinstance(parent, ast.If):
            side = (
                "true"
                if current in parent.body
                else "false"
                if current in parent.orelse
                else "test"
            )
            markers.append(
                f"if:{side}:{literal_base.canonical_ast(parent.test)}"
            )
        elif isinstance(parent, ast.While):
            side = (
                "body"
                if current in parent.body
                else "else"
                if current in parent.orelse
                else "test"
            )
            markers.append(
                f"while:{side}:{literal_base.canonical_ast(parent.test)}"
            )
        elif isinstance(parent, (ast.For, ast.AsyncFor)):
            side = (
                "body"
                if current in parent.body
                else "else"
                if current in parent.orelse
                else "iter"
            )
            markers.append(
                f"{'async-for' if isinstance(parent, ast.AsyncFor) else 'for'}:"
                f"{side}:{literal_base.canonical_ast(parent.iter)}"
            )
        elif isinstance(parent, ast.Try) or (
            try_star and isinstance(parent, try_star)
        ):
            if current in parent.body:
                markers.append("try:body")
            elif current in parent.orelse:
                markers.append("try:else")
            elif current in parent.finalbody:
                markers.append("try:finally")
        elif isinstance(parent, ast.ExceptHandler):
            markers.append(
                "except:"
                + (
                    "bare"
                    if parent.type is None
                    else literal_base.canonical_ast(parent.type)
                )
            )
        current = parent
    markers.reverse()
    return markers


def _receiver_aliases_before(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
    cutoff: int,
) -> set[str]:
    receiver_name = _root_name(receiver)
    if receiver_name is None:
        return set()

    aliases = {receiver_name}
    assignments = sorted(
        (
            item
            for item in ast.walk(function)
            if isinstance(item, (ast.Assign, ast.AnnAssign))
            and _belongs_to_function(item, function, parents)
            and getattr(item, "lineno", cutoff + 1) < cutoff
        ),
        key=lambda item: (
            getattr(item, "lineno", 0),
            getattr(item, "col_offset", 0),
        ),
    )

    for item in assignments:
        value = item.value
        value_root = _root_name(value)
        targets = item.targets if isinstance(item, ast.Assign) else [item.target]
        target_names = [
            target.id for target in targets if isinstance(target, ast.Name)
        ]
        for name in target_names:
            if value_root in aliases:
                aliases.add(name)
            elif name != receiver_name:
                aliases.discard(name)

    return aliases


def _target_touches_receiver(
    target: ast.AST,
    receiver: ast.AST,
    aliases: set[str],
) -> bool:
    target_path = _expression_path(target)
    receiver_path = _expression_path(receiver)
    if target_path is None or receiver_path is None:
        return False

    if len(receiver_path) == 1:
        return bool(target_path) and target_path[0] in aliases

    return target_path[: len(receiver_path)] == receiver_path


def _sink_receiver_state_history(
    node: ast.Call,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
) -> list[str]:
    function = _enclosing_function(node, parents)
    if function is None:
        return []

    cutoff = getattr(node, "lineno", 10**9)
    aliases = _receiver_aliases_before(function, receiver, parents, cutoff)
    receiver_name = _root_name(receiver)
    changes: list[tuple[int, int, str]] = []

    def record(item: ast.AST) -> None:
        line = getattr(item, "lineno", cutoff + 1)
        if line >= cutoff:
            return
        changes.append(
            (
                line,
                getattr(item, "col_offset", 0),
                json.dumps(
                    {
                        "context": _sink_state_context(item, function, parents),
                        "operation": literal_base.canonical_ast(item),
                    },
                    sort_keys=True,
                ),
            )
        )

    for item in ast.walk(function):
        if not _belongs_to_function(item, function, parents):
            continue

        if isinstance(item, ast.Assign):
            # Alias creation is not itself a sink mutation. Rebinding the actual
            # receiver, or mutating through a subscript/attribute target, is.
            for target in item.targets:
                if isinstance(target, ast.Name):
                    if target.id == receiver_name:
                        record(item)
                elif _target_touches_receiver(target, receiver, aliases):
                    record(item)
        elif isinstance(item, ast.AnnAssign):
            if isinstance(item.target, ast.Name):
                if item.target.id == receiver_name:
                    record(item)
            elif _target_touches_receiver(item.target, receiver, aliases):
                record(item)
        elif isinstance(item, ast.AugAssign):
            if _target_touches_receiver(item.target, receiver, aliases):
                record(item)
        elif isinstance(item, ast.NamedExpr):
            if _target_touches_receiver(item.target, receiver, aliases):
                record(item)
        elif isinstance(item, ast.Delete):
            if any(
                _target_touches_receiver(target, receiver, aliases)
                for target in item.targets
            ):
                record(item)
        elif (
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and _root_name(item.func.value) in aliases
            and item.func.attr in _DESTRUCTIVE_SINK_METHODS
        ):
            record(item)

    changes.sort()
    return [value for _, _, value in changes]


_original_sink_contract = sink_execution._emission_sink_contract


def _emission_sink_contract_with_receiver_state(
    node: ast.Call,
    parents: dict[int, ast.AST],
) -> list[str]:
    contract = list(_original_sink_contract(node, parents))
    receiver = _finding_sink_receiver(node, parents)
    if receiver is None:
        return contract

    state = _sink_receiver_state_history(node, receiver, parents)
    if state:
        contract.append("receiver-state:" + json.dumps(state, sort_keys=True))
    return contract


# The sink-aware semantic visitor installed by the preceding regression module
# resolves this module global when it executes, so this strengthens both the
# immutable published and current candidate signatures without rewriting the
# older scanner layers.
sink_execution._emission_sink_contract = _emission_sink_contract_with_receiver_state


_COMPOSED_PARAMETERIZED_VISIT_CALL = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Call
)


def _parameterized_contracts_for_call(visitor, node: ast.Call) -> list[str]:
    if not (
        isinstance(node.func, ast.Name)
        and node.func.id in visitor.parameterized_helpers
    ):
        return []

    helper_name = node.func.id
    definition = visitor.definitions[helper_name]
    contracts: list[str] = []

    for code_parameter in visitor.parameterized_helpers[helper_name]:
        code_argument = parameterized_active.base.call_argument(
            node, definition, code_parameter
        )
        if code_argument is None:
            continue
        code = parameterized_active.base.literal_string(
            code_argument, visitor.module_values
        )
        if code is None:
            continue

        arguments: dict[str, str] = {}
        all_parameters = parameterized_active.base.function_parameter_order(
            definition
        ) + [argument.arg for argument in definition.args.kwonlyargs]
        for parameter in all_parameters:
            if parameter == code_parameter:
                continue
            argument = parameterized_active.base.call_argument(
                node, definition, parameter
            )
            if argument is None:
                continue
            arguments[parameter] = parameterized_active.base.semantic_expression(
                argument,
                visitor.local_bindings,
                visitor.module_values,
                visitor.parameter_positions,
            )

        context = [
            {
                "branch": branch,
                "expression": parameterized_active.base.semantic_expression(
                    item,
                    visitor.local_bindings,
                    visitor.module_values,
                    visitor.parameter_positions,
                ),
            }
            for branch, item in visitor.context_nodes
        ]
        payload = {
            "sourcePath": visitor.source_path,
            "helper": helper_name,
            "caller": visitor.caller,
            "code": code,
            "context": context,
            "arguments": arguments,
        }
        if isinstance(definition, ast.AsyncFunctionDef):
            payload["helperExecution"] = (
                "async-generator:iteration-required"
                if generator_execution._function_is_generator(definition)
                else "coroutine:await-required"
            )
        contracts.append(json.dumps(payload, sort_keys=True))

    return contracts


def _is_parameterized_helper_call(visitor, node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Name)
        and node.func.id in visitor.parameterized_helpers
    )


class _CountingParameterizedCallSiteVisitor(
    parameterized_active.BranchAwareParameterizedCallSiteVisitor
):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.contract_counts: Counter[str] = Counter()

    def visit_Call(self, node: ast.Call) -> None:
        if _is_parameterized_helper_call(self, node):
            self.contract_counts.update(
                _parameterized_contracts_for_call(self, node)
            )
            self.generic_visit(node)
            return
        # Preserve all previously installed deferred lambda/generator execution
        # semantics for wrapper/eager-consumer calls.
        _COMPOSED_PARAMETERIZED_VISIT_CALL(self, node)


class _CountingReachableParameterizedCallSiteVisitor(
    parameterized_reachability.ReachableParameterizedCallSiteVisitor
):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.contract_counts: Counter[str] = Counter()

    def visit_Call(self, node: ast.Call) -> None:
        if _is_parameterized_helper_call(self, node):
            self.contract_counts.update(
                _parameterized_contracts_for_call(self, node)
            )
            self.generic_visit(node)
            return
        _COMPOSED_PARAMETERIZED_VISIT_CALL(self, node)


def _count_parameterized_contracts(
    text: str,
    source_path: str,
    visitor_type,
) -> Counter[str]:
    tree = ast.parse(text)
    helpers = parameterized_active.parameterized_finding_parameters(tree)
    if not helpers:
        return Counter()

    definitions = {
        statement.name: statement
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    visitor = visitor_type(
        source_path,
        definitions,
        helpers,
        parameterized_active.module_bindings(tree),
    )
    visitor.visit(tree)
    return visitor.contract_counts


def _reachable_parameterized_counts(text: str, source_path: str) -> Counter[str]:
    return _count_parameterized_contracts(
        text,
        source_path,
        _CountingReachableParameterizedCallSiteVisitor,
    )


def _published_reachable_parameterized_counts() -> Counter[str]:
    result: Counter[str] = Counter()
    for relative in parameterized_active.published_python_paths():
        result.update(
            _reachable_parameterized_counts(
                parameterized_active.git_source_at(
                    parameterized_active.CHECKPOINT_COMMIT,
                    relative,
                ),
                relative,
            )
        )
    return result


def _candidate_reachable_parameterized_counts() -> Counter[str]:
    result: Counter[str] = Counter()
    for path in parameterized_active.candidate_python_paths():
        relative = path.relative_to(parameterized_active.REPO_ROOT).as_posix()
        result.update(
            _reachable_parameterized_counts(
                path.read_text(encoding="utf-8"),
                relative,
            )
        )
    return result


class ReleaseCandidateLatestP1RegressionTests(unittest.TestCase):
    def test_rebinding_finding_sink_changes_semantic_contract(self):
        emitted = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        rebound = """
def validate(findings):
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        expected = literal_base.finding_semantic_signatures(emitted)
        actual = literal_base.finding_semantic_signatures(rebound)
        self.assertNotEqual(expected, actual)
        sink = json.loads(actual["PUBLIC_CODE"][0])["sink"]
        self.assertTrue(
            any(item.startswith("receiver-state:") for item in sink),
            sink,
        )

    def test_destructive_finding_sink_mutation_changes_semantic_contract(self):
        emitted = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        cleared = """
def validate(findings):
    findings.clear()
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        alias_cleared = """
def validate(findings):
    alias = findings
    alias.clear()
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        expected = literal_base.finding_semantic_signatures(emitted)
        self.assertNotEqual(
            expected,
            literal_base.finding_semantic_signatures(cleared),
        )
        self.assertNotEqual(
            expected,
            literal_base.finding_semantic_signatures(alias_cleared),
        )

    def test_additive_finding_append_does_not_rebind_existing_sink(self):
        original = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        additive = """
def validate(findings):
    findings.append(Finding("NEW_CODE", "new"))
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        expected = json.loads(
            literal_base.finding_semantic_signatures(original)["PUBLIC_CODE"][0]
        )["sink"]
        actual = json.loads(
            literal_base.finding_semantic_signatures(additive)["PUBLIC_CODE"][0]
        )["sink"]
        self.assertEqual(expected, actual)

    def test_every_published_reachable_parameterized_call_keeps_multiplicity(self):
        published = _published_reachable_parameterized_counts()
        candidate = _candidate_reachable_parameterized_counts()
        self.assertGreaterEqual(sum(published.values()), 8)

        changed = {
            contract: {
                "published": expected_count,
                "candidate": candidate.get(contract, 0),
            }
            for contract, expected_count in published.items()
            if candidate.get(contract, 0) != expected_count
        }
        self.assertEqual(
            changed,
            {},
            "published reachable parameterized finding call multiplicity changed",
        )

    def test_duplicate_parameterized_call_is_detected(self):
        single = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        duplicated = single.replace(
            '    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")',
            '    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")\n'
            '    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")',
        )
        expected = _reachable_parameterized_counts(single, "sample.py")
        actual = _reachable_parameterized_counts(duplicated, "sample.py")
        self.assertEqual(sum(expected.values()), 1)
        self.assertEqual(sum(actual.values()), 2)
        contract = next(iter(expected))
        self.assertEqual(expected[contract], 1)
        self.assertEqual(actual[contract], 2)

    def test_unreachable_duplicate_does_not_change_reachable_multiplicity(self):
        single = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        unreachable = single + """
    return
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        self.assertEqual(
            _reachable_parameterized_counts(single, "sample.py"),
            _reachable_parameterized_counts(unreachable, "sample.py"),
        )

    def test_distinct_new_parameterized_contract_remains_additive(self):
        published = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        additive = published.replace(
            '    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")',
            '    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")\n'
            '    read_text(root / "NOTICE", findings, "NOTICE_ENCODING")',
        )
        expected = _reachable_parameterized_counts(published, "sample.py")
        actual = _reachable_parameterized_counts(additive, "sample.py")
        for contract, count in expected.items():
            self.assertEqual(actual[contract], count)
        self.assertGreater(len(actual), len(expected))


if __name__ == "__main__":
    unittest.main()
