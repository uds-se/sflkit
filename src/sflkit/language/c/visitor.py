from pycparser import CParser
from pycparser.c_ast import NodeVisitor
from pycparser.c_generator import CGenerator

from sflkit.language.meta import MetaVisitor

from sflkit.language.visitor import ASTVisitor


class CInstrumentation(NodeVisitor, ASTVisitor):
    def __init__(self, meta_visitor: MetaVisitor):
        super().__init__(meta_visitor)

    def parse(self, source: str):
        return CParser().parse(source, self.file)

    def unparse(self, ast):
        return CGenerator().visit(ast)
