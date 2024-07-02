from abc import abstractmethod
from pathlib import Path
from typing import List, Optional

from sflkit import Config
from sflkit.language.visitor import ASTVisitor
from sflkit.mapping import EventMapping


class Instrumentation:
    def __init__(self, visitor: ASTVisitor, mapping_path: Optional[Path] = None):
        self.visitor = visitor
        self.events = EventMapping(path=mapping_path)

    @abstractmethod
    def instrument(
        self, src: str, dst: str, suffixes: List[str] = None, file: str = ""
    ):
        raise NotImplementedError()

    def dump_events(self, config: Config):
        self.events.write(config)


__all__ = ["dir_instrumentation", "file_instrumentation", "Instrumentation"]
