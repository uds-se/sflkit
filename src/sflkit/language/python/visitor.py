from ast import *
from typing import Any, Union

import astor

from sflkit.language.meta import MetaVisitor, Injection
from sflkit.language.python.extract import PythonIsDoc
from sflkit.language.python.factory import python_lib
from sflkit.language.visitor import ASTVisitor


class PythonInstrumentation(NodeTransformer, ASTVisitor):
    def __init__(self, meta_visitor: MetaVisitor):
        super().__init__(meta_visitor)
        self.is_doc = PythonIsDoc()
        self.__future__ = list()

    def parse(self, source: str):
        return parse(source)

    def start_visit(self, ast):
        self.__future__ = list()
        if isinstance(ast, Module) and ast.body and self.is_doc.visit(ast.body[0]):
            doc = [ast.body[0]]
            ast.body = ast.body[1:]
        else:
            doc = list()
        instrumented_tree = self.visit(ast)
        return Module(
            body=doc
            + self.__future__
            + [
                Import(names=[alias(name=python_lib, asname=None)]),
                instrumented_tree,
            ],
            type_ignores=list(),
        )

    def unparse(self, ast):
        return astor.to_source(ast)

    def __create_node(self, injection: Injection, node: AST, body=False, doc=None):
        doc = doc if doc else list()
        if injection.body:
            node.body = doc + injection.body + node.body
        elif doc and hasattr(node, "body"):
            node.body = doc + node.body
        if injection.body_last:
            node.body += injection.body_last
        if injection.orelse:
            node.orelse = injection.orelse + node.orelse
        if injection.assign:
            if hasattr(node, "value"):
                node.value = Name(id=injection.assign)
            elif hasattr(node, "test"):
                node.test = Name(id=injection.assign)
        if injection.finalbody:
            if hasattr(node, "finalbody"):
                node.finalbody = injection.finalbody + node.finalbody
            else:
                if body:
                    node.body = Try(
                        body=node.body,
                        handlers=[],
                        orelse=[],
                        finalbody=injection.finalbody,
                    )
                else:
                    node = Try(
                        body=[node],
                        handlers=[],
                        orelse=[],
                        finalbody=injection.finalbody,
                    )
        if injection.error:
            error_var = self.meta_visitor.tmp_generator.get_var_name()
            if body:
                node.body = (
                    Try(
                        body=node.body,
                        handlers=[
                            ExceptHandler(
                                type=Name(
                                    id="BaseException",
                                ),
                                name=error_var,
                                body=injection.error,
                            )
                        ],
                        orelse=[],
                        finalbody=[],
                    ),
                )
            else:
                node = (
                    Try(
                        body=[node],
                        handlers=[
                            ExceptHandler(
                                type=Name(
                                    id="BaseException",
                                ),
                                name=error_var,
                                body=injection.error,
                            )
                        ],
                        orelse=[],
                        finalbody=[],
                    ),
                )
        if injection.pre or injection.post:
            return Module(
                body=injection.pre + [node] + injection.post,
                type_ignores=list(),
            )
        return node

    def __visit_function(self, node: Union[FunctionDef, AsyncFunctionDef]) -> AST:
        self.meta_visitor.enter_function(node)
        injection = self.meta_visitor.visit_start(node)
        if self.is_doc.visit(node.body[0]):
            doc = [node.body[0]]
            body = node.body[1:]
        else:
            doc = None
            body = node.body
        node.body = [self.visit(n) for n in body]
        self.meta_visitor.exit_function(node)
        self.events += injection.events
        return self.__create_node(injection, node, body=True, doc=doc)

    def visit_FunctionDef(self, node: FunctionDef) -> AST:
        return self.__visit_function(node)

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> AST:
        return self.__visit_function(node)

    def visit_ClassDef(self, node: ClassDef) -> AST:
        self.meta_visitor.enter_class(node)
        injection = self.meta_visitor.visit_start(node)
        if self.is_doc.visit(node.body[0]):
            doc = [node.body[0]]
            body = node.body[1:]
        else:
            doc = None
            body = node.body
        node.body = [self.visit(n) for n in body]
        self.meta_visitor.exit_class(node)
        self.events += injection.events
        return self.__create_node(injection, node, doc=doc)

    def generic_visit(self, node: AST) -> AST:
        injection = self.meta_visitor.visit_start(node)
        self.events += injection.events
        super().generic_visit(node)
        return self.__create_node(injection, node)

    def _visit_import(self, node: Union[Import, ImportFrom]):
        if any(
            alias_.name == "__future__" for alias_ in node.names
        ):  # ignore __future__
            self.__future__.append(node)
            return
        return self.generic_visit(node)

    def visit_Import(self, node: Import) -> Any:
        return self._visit_import(node)

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        if node.module == "__future__":  # ignore __future__
            self.__future__.append(node)
            return
        return self._visit_import(node)
