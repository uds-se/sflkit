import logging
from abc import abstractmethod, ABC

from sflkit.language.meta import MetaVisitor


class ASTVisitor(ABC):
    def __init__(self, meta_visitor: MetaVisitor):
        self.meta_visitor = meta_visitor
        self.file = None
        self.events = list()

    @abstractmethod
    def parse(self, source: str):
        raise NotImplementedError()

    @abstractmethod
    def unparse(self, ast) -> str:
        raise NotImplementedError()

    @abstractmethod
    def start_visit(self, ast):
        raise NotImplementedError()

    def instrument(self, src: str, dst: str, file: str = ""):
        self.file = file
        with open(src, "r") as fp:
            source = fp.read()
        tree = self.parse(source)
        prev_events = len(self.events)
        self.meta_visitor.enter_file(self.file)
        instrumented_tree = self.start_visit(tree)
        self.meta_visitor.exit_file(self.file)
        with open(dst, "w") as fp:
            fp.write(self.unparse(instrumented_tree))
        logging.info(f"I found {len(self.events) - prev_events} events in {src}.")
