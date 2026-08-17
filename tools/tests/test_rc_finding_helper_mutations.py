from __future__ import annotations

import ast
import copy
import json
import unittest

import rc_finding_code_contracts_base as base
import test_rc_finding_code_contracts as finding_contracts


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


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _target_mutates_parameter(
    target: ast.AST,
    parameters: set[str],
    *,
    direct_name: bool,
) -> set[str]:
    mutated: set[str] = set()
    for item in ast.walk(target):
        if isinstance(item, (ast.Subscript, ast.Attribute)):
            root = _root_name(item)
            if root in parameters:
                mutated.add(root)
    if direct_name and isinstance(target, ast.Name) and target.id in parameters:
        mutated.add(target.id)
    return mutated


def _direct_mutated_parameters(
    helper: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    parameters = set(_parameter_names(helper))
    mutated: set[str] = set()

    class Visitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            return

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            return

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            return

        def visit_Assign(self, node: ast.Assign) -> None:
            for target in node.targets:
                mutated.update(
                    _target_mutates_parameter(
                        target,
                        parameters,
                        direct_name=False,
                    )
                )
            self.visit(node.value)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            mutated.update(
                _target_mutates_parameter(
                    node.target,
                    parameters,
                    direct_name=False,
                )
            )
            if node.value is not None:
                self.visit(node.value)

        def visit_AugAssign(self, node: ast.AugAssign) -> None:
            mutated.update(
                _target_mutates_parameter(
                    node.target,
                    parameters,
                    direct_name=True,
                )
            )
            self.visit(node.value)

        def visit_Delete(self, node: ast.Delete) -> None:
            for target in node.targets:
                mutated.update(
                    _target_mutates_parameter(
                        target,
                        parameters,
                        direct_name=False,
                    )
                )

        def visit_Call(self, node: ast.Call) -> None:
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in finding_contracts._MUTATING_METHODS
            ):
                root = _root_name(node.func.value)
                if root in parameters:
                    mutated.add(root)
            self.generic_visit(node)

    visitor = Visitor()
    for statement in helper.body:
        visitor.visit(statement)
    return mutated


def _argument_for_parameter(
    call: ast.Call,
    helper: ast.FunctionDef | ast.AsyncFunctionDef,
    parameter: str,
) -> list[ast.AST]:
    positional = [
        argument.arg for argument in (*helper.args.posonlyargs, *helper.args.args)
    ]
    if parameter in positional:
        index = positional.index(parameter)
        if index < len(call.args) and not isinstance(call.args[index], ast.Starred):
            return [call.args[index]]

    for keyword in call.keywords:
        if keyword.arg == parameter:
            return [keyword.value]

    if helper.args.vararg is not None and parameter == helper.args.vararg.arg:
        return [
            argument
            for argument in call.args[len(positional):]
            if not isinstance(argument, ast.Starred)
        ]
    if helper.args.kwarg is not None and parameter == helper.args.kwarg.arg:
        return [
            keyword.value
            for keyword in call.keywords
            if keyword.arg is not None
        ]
    return []


def _mutated_parameters(
    helper: ast.FunctionDef | ast.AsyncFunctionDef,
    helpers: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    stack: frozenset[str] = frozenset(),
) -> set[str]:
    if helper.name in stack:
        return _direct_mutated_parameters(helper)

    parameters = set(_parameter_names(helper))
    mutated = _direct_mutated_parameters(helper)
    next_stack = stack | {helper.name}

    class CallCollector(ast.NodeVisitor):
        def __init__(self) -> None:
            self.calls: list[ast.Call] = []

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            return

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            return

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            return

        def visit_Call(self, node: ast.Call) -> None:
            self.calls.append(node)
            self.generic_visit(node)

    collector = CallCollector()
    for statement in helper.body:
        collector.visit(statement)

    for call in collector.calls:
        if not isinstance(call.func, ast.Name):
            continue
        callee = helpers.get(call.func.id)
        if callee is None:
            continue
        callee_mutated = _mutated_parameters(callee, helpers, next_stack)
        for callee_parameter in callee_mutated:
            for argument in _argument_for_parameter(
                call,
                callee,
                callee_parameter,
            ):
                mutated.update(base.loaded_names(argument) & parameters)

    return mutated


def _helper_semantics(helper: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    cloned = copy.deepcopy(helper)
    cloned.name = "_helper"
    return base.normalized_semantic_ast(cloned)


def _normalized_helper_call(
    call: ast.Call,
    target: str,
    parameter_positions: dict[str, int],
    local_names: set[str],
) -> str:
    cloned = copy.deepcopy(call)
    if isinstance(cloned.func, ast.Name):
        cloned.func.id = "_helper"
    return finding_contracts._normalized_for_local(
        cloned,
        target,
        parameter_positions,
        local_names,
    )


def _finding_dependency_cutoffs(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    protected_codes: set[str],
) -> dict[str, int]:
    parents = finding_contracts._parent_map(function)
    parameters = set(_parameter_names(function))
    local_names = (
        finding_contracts._DependencyScopedBindingNormalizer._local_store_names(
            function
        )
        - parameters
    )
    bound_names = local_names | parameters
    cutoffs: dict[str, int] = {}

    for node in ast.walk(function):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "Finding"
            and base.finding_code(node) in protected_codes
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
            elif (
                isinstance(parent, ast.ExceptHandler)
                and parent.type is not None
            ):
                dependencies.append(parent.type)
            child = parent

        cutoff = getattr(node, "lineno", 0)
        for dependency in dependencies:
            for name in base.loaded_names(dependency) & bound_names:
                cutoffs[name] = max(cutoffs.get(name, 0), cutoff)

    bindings = finding_contracts._first_bindings(function, local_names)
    pending = [name for name in cutoffs if name in local_names]
    while pending:
        parent_name = pending.pop()
        binding = bindings.get(parent_name)
        if binding is None:
            continue
        for dependency_name in base.loaded_names(binding) & bound_names:
            inherited_cutoff = cutoffs[parent_name]
            if inherited_cutoff > cutoffs.get(dependency_name, 0):
                first_seen = dependency_name not in cutoffs
                cutoffs[dependency_name] = inherited_cutoff
                if dependency_name in local_names and first_seen:
                    pending.append(dependency_name)

    return cutoffs


def helper_mutation_contracts(
    text: str,
    source_path: str,
    protected_codes: set[str],
) -> set[str]:
    tree = ast.parse(text)
    helpers = {
        statement.name: statement
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    result: set[str] = set()

    for function in helpers.values():
        cutoffs = _finding_dependency_cutoffs(function, protected_codes)
        if not cutoffs:
            continue

        parameters = _parameter_names(function)
        parameter_positions = {
            name: index for index, name in enumerate(parameters)
        }
        local_names = (
            finding_contracts._DependencyScopedBindingNormalizer._local_store_names(
                function
            )
            - set(parameters)
        )
        bindings = finding_contracts._first_bindings(function, local_names)
        parents = finding_contracts._parent_map(function)

        for call in ast.walk(function):
            if not (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
            ):
                continue
            helper = helpers.get(call.func.id)
            if helper is None or helper is function:
                continue

            mutated_parameters = _mutated_parameters(helper, helpers)
            if not mutated_parameters:
                continue

            line = getattr(call, "lineno", 10**9)
            helper_parameters = _parameter_names(helper)

            for target, cutoff in cutoffs.items():
                if line > cutoff:
                    continue

                matched_positions: set[int] = set()
                for helper_parameter in mutated_parameters:
                    for argument in _argument_for_parameter(
                        call,
                        helper,
                        helper_parameter,
                    ):
                        if target in base.loaded_names(argument):
                            if helper_parameter in helper_parameters:
                                matched_positions.add(
                                    helper_parameters.index(helper_parameter)
                                )
                if not matched_positions:
                    continue

                if target in parameter_positions:
                    target_identity = (
                        f"parameter:{parameter_positions[target]}"
                    )
                else:
                    binding = bindings.get(target)
                    if binding is None:
                        target_identity = "local:store"
                    else:
                        target_identity = (
                            "local:"
                            + finding_contracts._normalized_for_local(
                                binding,
                                target,
                                parameter_positions,
                                local_names,
                            )
                        )

                payload = {
                    "sourcePath": source_path,
                    "function": function.name,
                    "target": target_identity,
                    "context": finding_contracts._branch_context(
                        call,
                        function,
                        parents,
                        target,
                        parameter_positions,
                        local_names,
                    ),
                    "call": _normalized_helper_call(
                        call,
                        target,
                        parameter_positions,
                        local_names,
                    ),
                    "mutatingParameterPositions": sorted(
                        matched_positions
                    ),
                    "helperSemantics": _helper_semantics(helper),
                }
                result.add(json.dumps(payload, sort_keys=True))

    return result


def published_helper_mutation_contracts() -> set[str]:
    protected_codes = set(base.published_signatures())
    result: set[str] = set()
    for source_path in base.published_python_paths():
        result.update(
            helper_mutation_contracts(
                base.git_source_at(base.CHECKPOINT_COMMIT, source_path),
                source_path,
                protected_codes,
            )
        )
    return result


def candidate_helper_mutation_contracts() -> set[str]:
    protected_codes = set(base.published_signatures())
    result: set[str] = set()
    for path in base.candidate_python_paths():
        source_path = path.relative_to(base.REPO_ROOT).as_posix()
        result.update(
            helper_mutation_contracts(
                path.read_text(encoding="utf-8"),
                source_path,
                protected_codes,
            )
        )
    return result


class ReleaseCandidateFindingHelperMutationTests(unittest.TestCase):
    def test_helper_mediated_mutation_contracts_match_published_source(self):
        self.assertEqual(
            candidate_helper_mutation_contracts(),
            published_helper_mutation_contracts(),
            (
                "helper-mediated mutations of published finding "
                "dependencies changed"
            ),
        )

    def test_helper_mutation_before_published_finding_is_detected(self):
        original = '''
def mark_seen(ids, key):
    ids[key] = "path"

def run(document_id):
    ids = {}
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        mutated = original.replace(
            "    if document_id in ids:\n",
            (
                "    mark_seen(ids, document_id)\n"
                "    if document_id in ids:\n"
            ),
        )
        self.assertNotEqual(
            helper_mutation_contracts(
                original,
                "<memory>",
                {"DUPLICATE_ID"},
            ),
            helper_mutation_contracts(
                mutated,
                "<memory>",
                {"DUPLICATE_ID"},
            ),
        )

    def test_helper_implementation_semantics_are_bound(self):
        original = '''
def mark_seen(ids, key):
    ids[key] = "path"

def run(document_id):
    ids = {}
    mark_seen(ids, document_id)
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        changed_helper = original.replace(
            '    ids[key] = "path"\n',
            "    ids.clear()\n",
        )
        self.assertNotEqual(
            helper_mutation_contracts(
                original,
                "<memory>",
                {"DUPLICATE_ID"},
            ),
            helper_mutation_contracts(
                changed_helper,
                "<memory>",
                {"DUPLICATE_ID"},
            ),
        )

    def test_pure_helper_use_does_not_create_mutation_contract(self):
        original = '''
def run(document_id):
    ids = {}
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        with_pure_helper = '''
def count_seen(ids):
    return len(ids)

def run(document_id):
    ids = {}
    count_seen(ids)
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        self.assertEqual(
            helper_mutation_contracts(
                original,
                "<memory>",
                {"DUPLICATE_ID"},
            ),
            helper_mutation_contracts(
                with_pure_helper,
                "<memory>",
                {"DUPLICATE_ID"},
            ),
        )


if __name__ == "__main__":
    unittest.main()
