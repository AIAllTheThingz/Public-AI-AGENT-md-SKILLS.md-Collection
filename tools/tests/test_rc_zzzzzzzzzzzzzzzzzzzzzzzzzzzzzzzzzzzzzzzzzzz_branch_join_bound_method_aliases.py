from __future__ import annotations

import ast
import json
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as sink_state
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_assignment_target_binding_and_path_sensitive_bound_aliases as previous


# A local callable may have different bindings on mutually exclusive branches
# and then be invoked after the branches join. Source-order last-write-wins is not
# the runtime semantics of that join. Preserve a destructive bound-method state
# whenever at least one feasible path to the common call retains that binding.
# A later binding shadows an earlier one only when it is guaranteed to execute on
# every path represented by the earlier binding.

older = previous.prior
post_sink = previous.post_sink


def _requirements(
    node: ast.AST,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[int, ast.AST],
) -> dict[str, bool]:
    return post_sink._if_requirements(node, function, parents)


def _merge_requirements(*items: dict[str, bool]) -> dict[str, bool] | None:
    merged: dict[str, bool] = {}
    for item in items:
        for key, value in item.items():
            existing = merged.get(key)
            if existing is not None and existing != value:
                return None
            merged[key] = value
    return merged


def _binding_targets_name(statement: ast.AST, name: str) -> bool:
    if isinstance(statement, ast.Assign):
        return any(isinstance(target, ast.Name) and target.id == name for target in statement.targets)
    if isinstance(statement, ast.AnnAssign):
        return isinstance(statement.target, ast.Name) and statement.target.id == name
    if isinstance(statement, ast.Delete):
        return any(isinstance(target, ast.Name) and target.id == name for target in statement.targets)
    return False


def _binding_value(statement: ast.AST) -> ast.AST | None:
    if isinstance(statement, ast.Assign):
        return statement.value
    if isinstance(statement, ast.AnnAssign):
        return statement.value
    return None


def _bindings_before(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    name: str,
    call: ast.Call,
    parents: dict[int, ast.AST],
) -> list[ast.AST]:
    cutoff = getattr(call, "lineno", 10**9)
    result = [
        item
        for item in ast.walk(function)
        if isinstance(item, (ast.Assign, ast.AnnAssign, ast.Delete))
        and sink_state._belongs_to_function(item, function, parents)
        and getattr(item, "lineno", cutoff + 1) < cutoff
        and _binding_targets_name(item, name)
    ]
    result.sort(
        key=lambda item: (
            getattr(item, "lineno", 0),
            getattr(item, "col_offset", 0),
        )
    )
    return result


def _later_binding_guaranteed_on_path(
    later: ast.AST,
    path_requirements: dict[str, bool],
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[int, ast.AST],
) -> bool:
    later_requirements = _requirements(later, function, parents)
    # The later binding is guaranteed only when every condition needed to reach
    # it is already fixed by the candidate path. Merely being compatible is not
    # enough: an extra condition may be false at runtime.
    return all(path_requirements.get(key) == value for key, value in later_requirements.items())


def _receiver_aliases_on_path(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    receiver: ast.AST,
    finding: ast.Call,
    binding: ast.AST,
    call: ast.Call,
    parents: dict[int, ast.AST],
) -> set[str]:
    return previous._path_receiver_aliases_before(
        function,
        receiver,
        finding,
        binding,
        call,
        parents,
        getattr(binding, "lineno", 0) + 1,
    )


def _direct_destructive_method(
    statement: ast.AST,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    receiver: ast.AST,
    finding: ast.Call,
    call: ast.Call,
    parents: dict[int, ast.AST],
) -> str | None:
    value = _binding_value(statement)
    if not (
        isinstance(value, ast.Attribute)
        and value.attr in sink_state._DESTRUCTIVE_SINK_METHODS
    ):
        return None

    receiver_aliases = _receiver_aliases_on_path(
        function,
        receiver,
        finding,
        statement,
        call,
        parents,
    )
    if sink_state._root_name(value.value) not in receiver_aliases:
        return None
    return value.attr


def _possible_destructive_method(
    name: str,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    receiver: ast.AST,
    finding: ast.Call,
    call: ast.Call,
    parents: dict[int, ast.AST],
    *,
    before_line: int | None = None,
    inherited_requirements: dict[str, bool] | None = None,
    seen: frozenset[tuple[str, int]] = frozenset(),
) -> str | None:
    bindings = _bindings_before(function, name, call, parents)
    if before_line is not None:
        bindings = [item for item in bindings if getattr(item, "lineno", 0) < before_line]

    finding_requirements = _requirements(finding, function, parents)
    call_requirements = _requirements(call, function, parents)
    inherited = inherited_requirements or {}

    for index, binding in enumerate(bindings):
        line = getattr(binding, "lineno", 0)
        marker = (name, line)
        if marker in seen:
            continue

        path = _merge_requirements(
            finding_requirements,
            call_requirements,
            inherited,
            _requirements(binding, function, parents),
        )
        if path is None:
            continue

        # If a later rebind is guaranteed on every execution represented by this
        # path, the current binding cannot reach the call. Mutually exclusive
        # later bindings are intentionally not considered shadows.
        shadowed = False
        for later in bindings[index + 1 :]:
            later_path = _merge_requirements(path, _requirements(later, function, parents))
            if later_path is None:
                continue
            if _later_binding_guaranteed_on_path(later, path, function, parents):
                shadowed = True
                break
        if shadowed:
            continue

        direct = _direct_destructive_method(
            binding,
            function,
            receiver,
            finding,
            call,
            parents,
        )
        if direct is not None:
            return direct

        value = _binding_value(binding)
        if isinstance(value, ast.Name):
            resolved = _possible_destructive_method(
                value.id,
                function,
                receiver,
                finding,
                call,
                parents,
                before_line=line,
                inherited_requirements=path,
                seen=seen | {marker},
            )
            if resolved is not None:
                return resolved

    return None


_previous_bound_aliases = previous._bound_destructive_aliases_before


def _bound_destructive_aliases_before(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    receiver: ast.AST,
    finding: ast.Call,
    call: ast.Call,
    parents: dict[int, ast.AST],
) -> dict[str, str]:
    aliases = dict(
        _previous_bound_aliases(
            function,
            receiver,
            finding,
            call,
            parents,
        )
    )
    if not isinstance(call.func, ast.Name):
        return aliases

    # Make the path-state query authoritative for the actually invoked local
    # callable. It both restores destructive states lost at branch joins and
    # removes source-order false positives that cannot reach this call.
    method = _possible_destructive_method(
        call.func.id,
        function,
        receiver,
        finding,
        call,
        parents,
    )
    aliases.pop(call.func.id, None)
    if method is not None:
        aliases[call.func.id] = method
    return aliases


# The post-emission history scanner defined in the older assignment layer looks
# this helper up in that module's globals at runtime.
previous._bound_destructive_aliases_before = _bound_destructive_aliases_before
older._bound_destructive_aliases_before = _bound_destructive_aliases_before


class ReleaseCandidateBranchJoinBoundMethodAliasTests(unittest.TestCase):
    def test_destructive_if_harmless_else_common_call_is_tracked(self) -> None:
        direct = '''
def harmless():
    return None

def validate(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        branch_join = '''
def harmless():
    return None

def validate(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    if flag:
        clear = findings.clear
    else:
        clear = harmless
    clear()
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(branch_join),
        )
        sink = json.loads(
            literal_base.finding_semantic_signatures(branch_join)["PUBLIC_CODE"][0]
        )["sink"]
        self.assertTrue(
            any(item.startswith("post-bound-method-receiver-state:") for item in sink),
            sink,
        )

    def test_harmless_if_destructive_else_common_call_is_tracked(self) -> None:
        direct = '''
def harmless():
    return None

def validate(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        branch_join = '''
def harmless():
    return None

def validate(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    if flag:
        clear = harmless
    else:
        clear = findings.clear
    clear()
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(branch_join),
        )

    def test_unconditional_harmless_rebind_shadows_branch_destructor(self) -> None:
        direct = '''
def harmless():
    return None

def validate(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        rebound = '''
def harmless():
    return None

def validate(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    if flag:
        clear = findings.clear
    clear = harmless
    clear()
'''
        direct_sink = json.loads(
            literal_base.finding_semantic_signatures(direct)["PUBLIC_CODE"][0]
        )["sink"]
        rebound_sink = json.loads(
            literal_base.finding_semantic_signatures(rebound)["PUBLIC_CODE"][0]
        )["sink"]
        self.assertEqual(direct_sink, rebound_sink)

    def test_same_branch_harmless_rebind_shadows_destructor(self) -> None:
        direct = '''
def harmless():
    return None

def validate(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        rebound = '''
def harmless():
    return None

def validate(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    if flag:
        clear = findings.clear
        clear = harmless
        clear()
'''
        direct_sink = json.loads(
            literal_base.finding_semantic_signatures(direct)["PUBLIC_CODE"][0]
        )["sink"]
        rebound_sink = json.loads(
            literal_base.finding_semantic_signatures(rebound)["PUBLIC_CODE"][0]
        )["sink"]
        self.assertEqual(direct_sink, rebound_sink)


if __name__ == "__main__":
    unittest.main()
