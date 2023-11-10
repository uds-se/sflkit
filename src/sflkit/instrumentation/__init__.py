import json
from abc import abstractmethod
from typing import List

from sflkitlib.events import event

from sflkit import Config
from sflkit.language.visitor import ASTVisitor
from sflkit.mapping import EventMapping


class Instrumentation:
    def __init__(self, visitor: ASTVisitor):
        self.visitor = visitor
        self.events = EventMapping()

    @abstractmethod
    def instrument(
        self, src: str, dst: str, suffixes: List[str] = None, file: str = ""
    ):
        raise NotImplementedError()

    def dump_events(self, config: Config):
        self.events.write(config)


__all__ = ["dir_instrumentation", "file_instrumentation", "Instrumentation"]
