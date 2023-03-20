import ast
import os
from typing import Set, Union

from sflkit.language.finder import (
    LocationsFinder,
    FunctionFinder,
    LoopFinder,
    BranchFinder,
)


class PythonLocationsFinder(ast.NodeVisitor, LocationsFinder):
    def get_locations(self, base_dir: str):
        if os.path.isfile(base_dir):
            base_dir = ""
        with open(os.path.join(base_dir, self.file), "r") as fp:
            s = fp.read()
        tree = ast.parse(s)
        self.visit(tree)
        return sorted(list(self.lines))

    def generic_visit(self, node: ast.AST) -> Set[int]:
        if hasattr(node, "lineno"):
            lines = {node.lineno}
        else:
            lines = set()
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        lines |= self.visit(item)
            elif isinstance(value, ast.AST):
                lines |= self.visit(value)
        return lines


class PythonFunctionFinder(PythonLocationsFinder, FunctionFinder):
    def visit_function(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        if node.lineno == self.line and node.name == self.target:
            lines = set(range(node.lineno, node.end_lineno + 1))
            self.lines |= lines
            return lines
        else:
            return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Set[int]:
        return self.visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Set[int]:
        return self.visit_function(node)


class PythonLoopFinder(PythonLocationsFinder, LoopFinder):
    def visit_loop(self, node: Union[ast.While, ast.For, ast.AsyncFor]):
        if node.lineno == self.line:
            lines = set(range(node.lineno, node.end_lineno + 1))
            self.lines |= lines
            return lines
        else:
            return self.generic_visit(node)

    def visit_While(self, node: ast.While) -> Set[int]:
        return self.visit_loop(node)

    def visit_For(self, node: ast.For) -> Set[int]:
        return self.visit_loop(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> Set[int]:
        return self.visit_loop(node)


class PythonBranchFinder(BranchFinder, PythonLocationsFinder):
    def visit_If(self, node: ast.If) -> Set[int]:
        if node.lineno == self.line:
            start = node.lineno
            end = node.test.end_lineno
            lines = set(range(start, end + 1))
            if self.then:
                start = node.lineno
                end = node.body[-1].end_lineno
            else:
                if len(node.orelse) > 0:
                    start = node.orelse[0].lineno
                    end = node.orelse[-1].end_lineno
            lines |= set(range(start, end + 1))
            self.lines |= lines
            return lines
        else:
            return self.generic_visit(node)
