import os
from pickle import PickleError

from sflkitlib.events import event

from sflkit.mapping import EventMapping


class EventFile(object):
    def __init__(
        self,
        path: os.PathLike,
        run_id: int,
        mapping: EventMapping,
        failing: bool = False,
    ):
        self.path = path
        self.run_id = run_id
        self.mapping = mapping
        self.failing = failing
        self._csv_reader = None
        self._file_pointer = None

    def __enter__(self):
        self._file_pointer = open(self.path, "rb")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file_pointer.close()

    def __repr__(self):
        return f'{self.path}:{self.run_id}:{"FAIL" if self.failing else "PASS"}'

    def __str__(self):
        return repr(self)

    def load(self):
        while self._file_pointer.peek(1):
            try:
                yield event.load_next_event(self._file_pointer, self.mapping.mapping)
            except (IndexError, ValueError, PickleError):
                break
