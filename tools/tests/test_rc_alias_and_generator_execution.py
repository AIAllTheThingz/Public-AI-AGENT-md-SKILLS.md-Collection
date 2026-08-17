from __future__ import annotations

import ast
import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as literal_base
import rc_parameterized_finding_codes_base as parameterized_base
import test_rc_approved_helper_and_deferred_execution as deferred_execution
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_code_contracts as finding_contracts
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability


# ---------------------------------------------------------------------------
# Alias-aware mutation history
# ---------------------------------------------------------------------------

_original_target_mutation_history = finding_contracts._target_mutation_history


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, (ast.Subscript, ast.Attribute)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _in_function_scope(
    node: ast.AST,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    current = node
    while current in parents:
        current = parents[current]
        if current is function:
            return True
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            return False
    return False


def _alias_mutation_history(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    target: str,
    cutoff: int,
    parameter_positions: dict[str, int],
    local_names: set[str],
) -> list[str]:
    parents = finding_contracts._parent_map(function)
    aliases: set[str] = {target}
    mutations: list[tuple[int, int, str]] = []

    nodes = [
        node
        for node in ast.walk(function)
        if _in_function_scope(node, function, parents)
        and 0 < getattr(node, "lineno", 0) <= cutoff
    ]
    nodes.sort(key=lambda node: (getattr(node, "lineno", 0), getattr(node, "col_offset", 0)))

    def add(node: ast.AST) -> None:
        context = finding_contracts._branch_context(
            node,
            function,
            parents,
            target,
            parameter_positions,
            local_names,
        )
        mutations.append(
            (
                getattr(node, "lineno", cutoff + 1),
                getattr(node, "col_offset", 0),
                "|".join(
                    context
                    + [
                        finding_contracts._normalized_for_local(
                            node,
                            target,
                            parameter_positions,
                            local_names,
                        )
                    ]
                ),
            )
        )

    def mutation_roots(target_node: ast.AST) -> set[str]:
        roots: set[str] = set()
        for item in ast.walk(target_node):
            if isinstance(item, (ast.Subscript, ast.Attribute)):
                root = _root_name(item)
                if root is not None:
                    roots.add(root)
        return roots

    for node in nodes:
        if isinstance(node, ast.AugAssign):
            roots = mutation_roots(node.target)
            if any(root in aliases and root != target for root in roots):
                add(node)
            continue

        if isinstance(node, ast.Delete):
            roots = set().union(*(mutation_roots(item) for item in node.targets))
            if any(root in aliases and root != target for root in roots):
                add(node)
            continue

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in finding_contracts._MUTATING_METHODS
        ):
            root = _root_name(node.func.value)
            if root in aliases and root != target:
                add(node)
            continue

        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue

        assignment_targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        roots = set().union(*(mutation_roots(item) for item in assignment_targets))
        if any(root in aliases and root != target for root in roots):
            add(node)

        value = node.value
        source_alias = isinstance(value, ast.Name) and value.id in aliases
        name_targets = [item for item in assignment_targets if isinstance(item, ast.Name)]

        # A direct rebind of the tracked name invalidates aliases of its previous
        # object unless the new value is itself one of those aliases.
        if any(item.id == target for item in name_targets) and not source_alias:
            aliases = {target}

        for item in name_targets:
            if item.id == target:
                continue
            if source_alias:
                aliases.add(item.id)
            else:
                aliases.discard(item.id)

    mutations.sort()
    return [item[2] for item in mutations]


def _target_mutation_history_with_aliases(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    target: str,
    cutoff: int,
    parameter_positions: dict[str, int],
    local_names: set[str],
) -> list[str]:
    direct = _original_target_mutation_history(
        function,
        target,
        cutoff,
        parameter_positions,
        local_names,
    )
    aliases = _alias_mutation_history(
        function,
        target,
        cutoff,
        parameter_positions,
        local_names,
    )
    return [*direct, *aliases]


finding_contracts._target_mutation_history = _target_mutation_history_with_aliases


# ---------------------------------------------------------------------------
# Generator-expression execution semantics
# ---------------------------------------------------------------------------

_EAGER_GENERATOR_CONSUMERS = {
    "all",
    "any",
    "dict",
    "frozenset",
    "list",
    "max",
    "min",
    "next",
    "set",
    "sorted",
    "sum",
    "tuple",
}


def _visit_generator_creation(visitor: ast.NodeVisitor, node: ast.GeneratorExp) -> None:
    # Python evaluates the outermost iterable when the generator object is
    # created, but the filters, nested iterables, and element expression are
    # deferred until iteration.
    if node.generators:
        visitor.visit(node.generators[0].iter)


def _visit_generator_body(visitor: ast.NodeVisitor, node: ast.GeneratorExp) -> None:
    for index, generator in enumerate(node.generators):
        if index:
            visitor.visit(generator.iter)
        for condition in generator.ifs:
            visitor.visit(condition)
    visitor.visit(node.elt)


def _generator_from_expression(visitor, expression: ast.AST) -> ast.GeneratorExp | None:
    if isinstance(expression, ast.GeneratorExp):
        return expression
    if not isinstance(expression, ast.Name):
        return None
    for attribute in (
        "_deferred_generators",
        "local_bindings",
        "module_definitions",
        "module_values",
    ):
        bindings = getattr(visitor, attribute, {})
        binding = bindings.get(expression.id)
        if isinstance(binding, ast.GeneratorExp):
            return binding
    return None


def _call_consumer_name(node: ast.Call) -> str | None:
    return node.func.id if isinstance(node.func, ast.Name) else None


# Literal semantic signatures.
_literal_visit_call_after_lambda = literal_base.FindingSignatureVisitor.visit_Call


def _literal_visit_generator(self, node: ast.GeneratorExp) -> None:
    _visit_generator_creation(self, node)


def _literal_visit_call_with_generators(self, node: ast.Call) -> None:
    _literal_visit_call_after_lambda(self, node)
    if _call_consumer_name(node) not in _EAGER_GENERATOR_CONSUMERS:
        return
    for argument in node.args:
        generator = _generator_from_expression(self, argument)
        if generator is None:
            continue
        marker = id(generator)
        active = getattr(self, "_active_generator_bodies", set())
        if marker in active:
            continue
        previous = active
        self._active_generator_bodies = set(active) | {marker}
        self.context.append("generator:iterated")
        try:
            _visit_generator_body(self, generator)
        finally:
            self.context.pop()
            self._active_generator_bodies = previous


literal_base.FindingSignatureVisitor.visit_GeneratorExp = _literal_visit_generator
literal_base.FindingSignatureVisitor.visit_Call = _literal_visit_call_with_generators


# Literal reachability scanners.
def _patch_reachability_generators(visitor_type) -> None:
    original_init = visitor_type.__init__
    original_assign = visitor_type.visit_Assign
    original_annassign = visitor_type.visit_AnnAssign
    original_call = visitor_type.visit_Call

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self._deferred_generators: dict[str, ast.GeneratorExp] = {}
        self._active_generator_bodies: set[int] = set()

    def visit_generator(self, node: ast.GeneratorExp) -> None:
        _visit_generator_creation(self, node)

    def visit_assign(self, node: ast.Assign) -> None:
        original_assign(self, node)
        for target in node.targets:
            if isinstance(target, ast.Name):
                if isinstance(node.value, ast.GeneratorExp):
                    self._deferred_generators[target.id] = node.value
                else:
                    self._deferred_generators.pop(target.id, None)

    def visit_annassign(self, node: ast.AnnAssign) -> None:
        original_annassign(self, node)
        if isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.GeneratorExp):
                self._deferred_generators[node.target.id] = node.value
            else:
                self._deferred_generators.pop(node.target.id, None)

    def visit_call(self, node: ast.Call) -> None:
        original_call(self, node)
        if _call_consumer_name(node) not in _EAGER_GENERATOR_CONSUMERS:
            return
        for argument in node.args:
            generator = _generator_from_expression(self, argument)
            if generator is None:
                continue
            marker = id(generator)
            if marker in self._active_generator_bodies:
                continue
            self._active_generator_bodies.add(marker)
            try:
                _visit_generator_body(self, generator)
            finally:
                self._active_generator_bodies.remove(marker)

    visitor_type.__init__ = patched_init
    visitor_type.visit_GeneratorExp = visit_generator
    visitor_type.visit_Assign = visit_assign
    visitor_type.visit_AnnAssign = visit_annassign
    visitor_type.visit_Call = visit_call


_patch_reachability_generators(basic_reachability.ReachableFindingVisitor)
_patch_reachability_generators(extended_reachability.ExtendedReachableFindingVisitor)


# Parameterized helper discovery. This preserves the lambda handling installed by
# the previous remediation and adds deferred generator bodies plus explicit eager
# consumers.
def _execution_aware_parameterized_finding_parameters_with_generators(
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
                self.generators: dict[str, ast.GeneratorExp] = {}
                self.active_lambdas: set[int] = set()
                self.active_generators: set[int] = set()

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                return

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                return

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                return

            def visit_Lambda(self, node: ast.Lambda) -> None:
                deferred_execution._visit_lambda_defaults(self, node)

            def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
                _visit_generator_creation(self, node)

            def visit_Assign(self, node: ast.Assign) -> None:
                self.visit(node.value)
                for target in node.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    if isinstance(node.value, ast.Lambda):
                        self.lambdas[target.id] = node.value
                    else:
                        self.lambdas.pop(target.id, None)
                    if isinstance(node.value, ast.GeneratorExp):
                        self.generators[target.id] = node.value
                    else:
                        self.generators.pop(target.id, None)

            def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
                if node.value is not None:
                    self.visit(node.value)
                if not isinstance(node.target, ast.Name):
                    return
                if isinstance(node.value, ast.Lambda):
                    self.lambdas[node.target.id] = node.value
                else:
                    self.lambdas.pop(node.target.id, None)
                if isinstance(node.value, ast.GeneratorExp):
                    self.generators[node.target.id] = node.value
                else:
                    self.generators.pop(node.target.id, None)

            def visit_Call(self, node: ast.Call) -> None:
                if isinstance(node.func, ast.Name) and node.func.id == "Finding":
                    expression = parameterized_base.finding_code_expression(node)
                    if isinstance(expression, ast.Name) and expression.id in parameters:
                        used.add(expression.id)

                deferred_lambda = None
                if isinstance(node.func, ast.Lambda):
                    deferred_lambda = node.func
                elif isinstance(node.func, ast.Name):
                    deferred_lambda = self.lambdas.get(node.func.id)
                if deferred_lambda is not None:
                    if isinstance(node.func, ast.Lambda):
                        self.visit(node.func)
                    for argument in node.args:
                        self.visit(argument)
                    for keyword in node.keywords:
                        self.visit(keyword.value)
                    marker = id(deferred_lambda)
                    if marker not in self.active_lambdas:
                        self.active_lambdas.add(marker)
                        try:
                            self.visit(deferred_lambda.body)
                        finally:
                            self.active_lambdas.remove(marker)
                    return

                self.generic_visit(node)
                if _call_consumer_name(node) not in _EAGER_GENERATOR_CONSUMERS:
                    return
                for argument in node.args:
                    generator = None
                    if isinstance(argument, ast.GeneratorExp):
                        generator = argument
                    elif isinstance(argument, ast.Name):
                        generator = self.generators.get(argument.id)
                    if generator is None:
                        continue
                    marker = id(generator)
                    if marker in self.active_generators:
                        continue
                    self.active_generators.add(marker)
                    try:
                        _visit_generator_body(self, generator)
                    finally:
                        self.active_generators.remove(marker)

        visitor = Visitor()
        for body_statement in statement.body:
            visitor.visit(body_statement)
        if used:
            result[statement.name] = used
    return result


parameterized_base.parameterized_finding_parameters = (
    _execution_aware_parameterized_finding_parameters_with_generators
)
parameterized_active.base.parameterized_finding_parameters = (
    _execution_aware_parameterized_finding_parameters_with_generators
)
parameterized_active.parameterized_finding_parameters = (
    _execution_aware_parameterized_finding_parameters_with_generators
)


# Parameterized call-site semantic and reachability visitors.
_parameterized_visit_call_after_lambda = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Call
)


def _parameterized_visit_generator(self, node: ast.GeneratorExp) -> None:
    _visit_generator_creation(self, node)


def _parameterized_visit_call_with_generators(self, node: ast.Call) -> None:
    _parameterized_visit_call_after_lambda(self, node)
    if _call_consumer_name(node) not in _EAGER_GENERATOR_CONSUMERS:
        return
    for argument in node.args:
        generator = _generator_from_expression(self, argument)
        if generator is None:
            continue
        marker = id(generator)
        active = getattr(self, "_active_generator_bodies", set())
        if marker in active:
            continue
        previous = active
        self._active_generator_bodies = set(active) | {marker}
        self.context_nodes.append(
            ("generator:iterated", ast.Constant(value="generator"))
        )
        try:
            _visit_generator_body(self, generator)
        finally:
            self.context_nodes.pop()
            self._active_generator_bodies = previous


parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_GeneratorExp = (
    _parameterized_visit_generator
)
parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Call = (
    _parameterized_visit_call_with_generators
)


class ReleaseCandidateAliasAndGeneratorExecutionTests(unittest.TestCase):
    def test_subscript_mutation_through_alias_changes_dependency_identity(self):
        original = '''
def run(document_id):
    ids = {}
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        mutated = original.replace(
            "    if document_id in ids:\n",
            (
                "    alias = ids\n"
                '    alias[document_id] = "path"\n'
                "    if document_id in ids:\n"
            ),
        )
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(original),
            literal_base.finding_semantic_signatures(mutated),
        )

    def test_transitive_alias_mutation_changes_dependency_identity(self):
        original = '''
def run(document_id):
    ids = {}
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        mutated = original.replace(
            "    if document_id in ids:\n",
            (
                "    first = ids\n"
                "    second = first\n"
                "    second.clear()\n"
                "    if document_id in ids:\n"
            ),
        )
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(original),
            literal_base.finding_semantic_signatures(mutated),
        )

    def test_rebound_alias_does_not_create_false_dependency_mutation(self):
        original = '''
def run(document_id):
    ids = {}
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        unrelated = original.replace(
            "    if document_id in ids:\n",
            (
                "    alias = ids\n"
                "    alias = {}\n"
                '    alias[document_id] = "unrelated"\n'
                "    if document_id in ids:\n"
            ),
        )
        self.assertEqual(
            literal_base.finding_semantic_signatures(original),
            literal_base.finding_semantic_signatures(unrelated),
        )

    def test_discarded_literal_generator_body_is_not_semantic_emission(self):
        discarded = '''
def validate():
    (Finding("PUBLIC_CODE", "hidden", path="sample") for _ in ())
'''
        consumed = '''
def validate():
    list(Finding("PUBLIC_CODE", "visible", path="sample") for _ in [1])
'''
        self.assertNotIn(
            "PUBLIC_CODE", literal_base.finding_semantic_signatures(discarded)
        )
        self.assertIn(
            "PUBLIC_CODE", literal_base.finding_semantic_signatures(consumed)
        )

    def test_discarded_literal_generator_body_is_not_reachable(self):
        discarded = '''
def validate():
    (Finding("PUBLIC_CODE", "hidden") for _ in ())
'''
        consumed = '''
def validate():
    list(Finding("PUBLIC_CODE", "visible") for _ in [1])
'''
        self.assertEqual(
            extended_reachability.reachable_contracts(discarded, "sample.py"),
            Counter(),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(consumed, "sample.py")[
                ("sample.py", "validate", "PUBLIC_CODE")
            ],
            1,
        )

    def test_assigned_generator_requires_consumption(self):
        discarded = '''
def validate():
    deferred = (Finding("PUBLIC_CODE", "hidden") for _ in [1])
'''
        consumed = discarded + "    list(deferred)\n"
        self.assertEqual(
            extended_reachability.reachable_contracts(discarded, "sample.py"),
            Counter(),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(consumed, "sample.py")[
                ("sample.py", "validate", "PUBLIC_CODE")
            ],
            1,
        )

    def test_parameterized_helper_discovery_ignores_discarded_generator(self):
        discarded = '''
def emit(code):
    (Finding(code, "hidden") for _ in ())
'''
        consumed = '''
def emit(code):
    list(Finding(code, "visible") for _ in [1])
'''
        self.assertEqual(
            _execution_aware_parameterized_finding_parameters_with_generators(
                ast.parse(discarded)
            ),
            {},
        )
        self.assertEqual(
            _execution_aware_parameterized_finding_parameters_with_generators(
                ast.parse(consumed)
            ),
            {"emit": {"code"}},
        )

    def test_parameterized_call_site_requires_generator_consumption(self):
        discarded = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    (read_text(root / "LICENSE", findings, "LICENSE_ENCODING") for _ in ())
'''
        consumed = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    list(read_text(root / "LICENSE", findings, "LICENSE_ENCODING") for _ in [1])
'''
        self.assertEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                discarded, "sample.py"
            ),
            set(),
        )
        contracts = parameterized_reachability.reachable_parameterized_contracts(
            consumed, "sample.py"
        )
        self.assertEqual(len(contracts), 1)
        self.assertEqual(json.loads(next(iter(contracts)))["code"], "LICENSE_ENCODING")


if __name__ == "__main__":
    unittest.main()
