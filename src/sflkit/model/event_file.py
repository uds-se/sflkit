import csv

from sflkit.events import event


class EventFile(object):
    def __init__(self, path: str, run_id: int, failing: bool = False):
        self.path = path
        self.run_id = run_id
        self.failing = failing
        self._csv_reader = None
        self._file_pointer = None

    def __enter__(self):
        self._file_pointer = open(self.path, "r")
        self._csv_reader = csv.reader(self._file_pointer)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file_pointer.close()

    def __repr__(self):
        return f'{self.path}:{self.run_id}:{"FAIL" if self.failing else "PASS"}'

    def __str__(self):
        return repr(self)

    def load(self):
        for row in self._csv_reader:
            yield event.load_event(event.EventType(int(row[0])), *row[1:])
