import json
from typing import List

from sflkit.events import event
from sflkit.language.visitor import ASTVisitor


class Instrumentation(object):

    def __init__(self, visitor: ASTVisitor):
        self.visitor = visitor
        self.events = list()

    def instrument(self, src: str, dst: str, suffixes: List[str] = None, file: str = ''):
        pass

    def dump_events(self, out_file):
        with open(out_file, 'w') as fp:
            json.dump(self.events, fp, cls=event.EventEncoder)


__all__ = ['dir_instrumentation', 'file_instrumentation', 'lib', 'Instrumentation']
