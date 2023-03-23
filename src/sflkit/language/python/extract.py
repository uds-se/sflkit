import ast
from typing import Any, Union

from sortedcollections import OrderedSet

from sflkit.events.event import ConditionEvent
from sflkit.language.extract import VariableExtract, ConditionExtract


class PythonIsDoc(ast.NodeVisitor):
    def generic_visit(self, node: ast.AST) -> bool:
        return False

    def visit_Expr(self, node: ast.Expr) -> bool:
        return self.visit(node.value)

    def visit_Constant(self, node: ast.Constant) -> bool:
        return isinstance(node.value, str)


class PythonVarExtract(ast.NodeVisitor, VariableExtract):
    def __init__(self, use=False):
        self.use = use
        self.current_ignores = set()
        self.ignores = list()

    def enter_ignores(self):
        self.ignores.append(self.current_ignores)
        self.current_ignores = set(self.current_ignores)

    def exit_ignores(self):
        self.current_ignores = self.ignores.pop()

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        variables = list()
        if node:
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            variables += self.visit(item)
                elif isinstance(value, ast.AST):
                    variables += self.visit(value)
        return OrderedSet(variables)

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        variables = self.visit(node.value)
        if isinstance(node.value, ast.Name):
            return (variables if self.use else {}) | OrderedSet(
                f"{variable}.{node.attr}"
                for variable in variables
                if variable not in self.current_ignores
            )
        else:
            return variables

    def visit_Tuple(self, node: ast.Tuple):
        targets = OrderedSet()
        for target in node.elts:
            targets |= self.visit(target)
        return targets

    def visit_Name(self, node: ast.Name):
        if node.id == "_":
            return OrderedSet()
        return OrderedSet({node.id})

    def visit_arguments(self, node: ast.arguments) -> Any:
        return OrderedSet(value for arg in node.args for value in self.visit(arg))

    def visit_arg(self, node: ast.arg):
        return OrderedSet({node.arg})

    def visit_Starred(self, node: ast.Starred):
        return OrderedSet(value for value in self.visit(node.value))

    def visit_withitem(self, node: ast.withitem):
        if node.optional_vars is None:
            return OrderedSet()
        return self.visit(node.optional_vars)

    def visit_alias(self, node: ast.alias):
        if node.asname is None:
            return OrderedSet({node.name})
        else:
            return OrderedSet({node.asname})

    def visit_Subscript(self, node: ast.Subscript) -> Any:
        if self.use:
            return self.generic_visit(node)
        else:
            return OrderedSet()

    def visit_keyword(self, node: ast.keyword) -> Any:
        return self.visit(node.value)

    def visit_Call(self, node: ast.Call) -> Any:
        variables = self.visit(node.func)
        return (
            OrderedSet(
                var for arg in node.args + node.keywords for var in self.visit(arg)
            )
            | variables
        )

    def visit_comprehension(self, node: ast.comprehension) -> Any:
        self.current_ignores |= self.visit(node.target)
        return self.generic_visit(node)

    def _visit_gen(
        self, node: Union[ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp]
    ):
        self.enter_ignores()
        variables = self.generic_visit(node) - self.current_ignores
        self.exit_ignores()
        return variables

    def visit_ListComp(self, node: ast.ListComp) -> Any:
        return self._visit_gen(node)

    def visit_SetComp(self, node: ast.SetComp) -> Any:
        return self._visit_gen(node)

    def visit_DictComp(self, node: ast.DictComp) -> Any:
        return self._visit_gen(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> Any:
        return self._visit_gen(node)

    def visit_Lambda(self, node: ast.Lambda) -> Any:
        self.enter_ignores()
        self.current_ignores.update(self.visit(node.args))
        variables = self.visit(node.body) - self.current_ignores
        self.exit_ignores()
        return variables

    def visit_Global(self, node: ast.Global) -> Any:
        return OrderedSet(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> Any:
        return OrderedSet(node.names)


class PythonConditionExtract(ast.NodeVisitor, ConditionExtract):
    def __init__(self):
        self.factory = None
        self.file = None

    def setup(self, factory):
        self.file = factory.file
        self.factory = factory

    def __get_tmp_var(self, val: ast.AST, expression: str):
        var = self.factory.tmp_generator.get_var_name()
        e = ConditionEvent(
            self.file,
            val.lineno,
            self.factory.id_generator.get_next_id(),
            expression,
            tmp_var=var,
        )
        return (
            var,
            ast.Name(id=var),
            ast.Module(
                body=[
                    ast.Assign(
                        targets=[
                            ast.Name(
                                id=var,
                            ),
                        ],
                        value=val,
                        type_comment=None,
                    ),
                    self.factory.get_event_call(e),
                ],
                type_ignores=list(),
            ),
            [e],
        )

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        return self.__get_tmp_var(node, ast.unparse(node))

    @staticmethod
    def __get_if(test, body):
        return ast.If(
            test=test,
            body=[
                body,
            ],
            orelse=[],
        )

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        tmp_vars = [self.visit(n) for n in node.values]
        es = list()
        if isinstance(node.op, ast.And):
            _, use_, assign, e = tmp_vars[-1]
            es.append(e)
            variables = [use_]
            for var_, use_, assign_, events in reversed(tmp_vars[:-1]):
                variables.append(use_)
                es += events
                assign = ast.Module(
                    body=[assign_, self.__get_if(use_, assign)],
                    type_ignores=list(),
                )
        else:
            _, use_, assign, events = tmp_vars[-1]
            es += events
            variables = [use_]
            for var_, use_, assign_, events in reversed(tmp_vars[:-1]):
                variables.append(use_)
                es += events
                assign = ast.Module(
                    body=[
                        assign_,
                        self.__get_if(ast.UnaryOp(op=ast.Not(), operand=use_), assign),
                    ],
                    type_ignores=list(),
                )

        expression = ast.unparse(node)
        final_var, final_use, final_assign, e = self.__get_tmp_var(
            ast.BoolOp(
                op=node.op, values=list(reversed(variables)), lineno=node.lineno
            ),
            expression,
        )
        es += e
        return (
            final_var,
            final_use,
            ast.Module(
                body=[
                    assign,
                    final_assign,
                ],
                type_ignores=list(),
            ),
            es,
        )

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        if isinstance(node.op, ast.Not):
            var, use, assign, events = self.visit(node.operand)
            expression = ast.unparse(node)
            final_var, final_use, final_assign, es = self.__get_tmp_var(
                ast.UnaryOp(op=node.op, operand=use, lineno=node.lineno), expression
            )
            return (
                final_var,
                final_use,
                ast.Module(
                    body=[
                        assign,
                        final_assign,
                    ],
                    type_ignores=list(),
                ),
                events + es,
            )
        else:
            return self.generic_visit(node)

    def visit_Expr(self, node: ast.Expr) -> Any:
        return self.visit(node.value)
