import json
from abc import abstractmethod
from typing import List

from sflkit.events import event
from sflkit.language.visitor import ASTVisitor


class Instrumentation:
    def __init__(self, visitor: ASTVisitor):
        self.visitor = visitor
        self.events = list()

    @abstractmethod
    def instrument(
        self, src: str, dst: str, suffixes: List[str] = None, file: str = ""
    ):
        raise NotImplementedError()

    def dump_events(self, out_file):
        with open(out_file, "w") as fp:
            json.dump(self.events, fp, cls=event.EventEncoder)


__all__ = ["dir_instrumentation", "file_instrumentation", "lib", "Instrumentation"]
