from typing import List

from sflkit.instrumentation import Instrumentation
from sflkit.language.visitor import ASTVisitor


class FileInstrumentation(Instrumentation):
    def __init__(self, visitor: ASTVisitor):
        super().__init__(visitor)

    def instrument(
        self, src: str, dst: str, suffixes: List[str] = None, file: str = ""
    ):
        self.visitor.instrument(src, dst, file)
        self.events = self.visitor.events[:]
