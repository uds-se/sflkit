from typing import List


class Location(object):
    def __init__(self, file: str, line: int):
        self.file = file
        self.line = line

    def __repr__(self):
        return f"{self.file}:{self.line}"

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return (
            isinstance(other, Location)
            and other.file == self.file
            and other.line == self.line
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.file, self.line))


class Suggestion(object):
    def __init__(self, lines: List[Location], suspiciousness: float):
        self.lines = lines
        self.suspiciousness = suspiciousness

    def __repr__(self):
        return f"{self.lines}:{self.suspiciousness}"

    def __str__(self):
        return repr(self)

    def __lt__(self, other):
        return other > self.suspiciousness

    def __gt__(self, other):
        return other < self.suspiciousness

    def __le__(self, other):
        return other >= self.suspiciousness

    def __ge__(self, other):
        return other <= self.suspiciousness

    def __len__(self):
        return len(self.lines)
