import enum
from abc import abstractmethod
from typing import List, Type

from sflkit.model.scope import Scope


class AnalysisType(enum.Enum):
    LINE = 0
    BRANCH = 1
    FUNCTION = 2
    LOOP = 3
    DEF_USE = 4
    CONDITION = 5
    SCALAR_PAIR = 6
    VARIABLE = 7
    RETURN = 8
    NONE = 9
    EMPTY_STRING = 10
    ASCII_STRING = 11
    DIGIT_STRING = 12
    SPECIAL_STRING = 13
    EMPTY_BYTES = 14


"""
If you want to add new spectra or predicates, please register them here and in sflkit/language/.py
"""


class AnalysisObject(object):

    function_finder = None
    loop_finder = None
    branch_finder = None

    @staticmethod
    def set_finder(function_finder, loop_finder, branch_finder):
        AnalysisObject.function_finder = function_finder
        AnalysisObject.loop_finder = loop_finder
        AnalysisObject.branch_finder = branch_finder

    # noinspection PyUnusedLocal
    def __init__(self, event):
        self.suspiciousness: float = 0

    def __repr__(self):
        return f"{self.analysis_type()}:{self.suspiciousness}"

    def __str__(self):
        return repr(self)

    @staticmethod
    @abstractmethod
    def analysis_type() -> AnalysisType:
        raise NotImplementedError()

    def analyze(self, passed: List, failed: List):
        self.finalize(passed, failed)
        self.calculate()

    def calculate(self):
        pass

    @abstractmethod
    def finalize(self, passed: List, failed: List):
        raise NotImplementedError()

    @abstractmethod
    def hit(self, id_, event, scope_: Scope = None):
        raise NotImplementedError()

    @abstractmethod
    def get_suggestion(self):
        raise NotImplementedError()

    @abstractmethod
    def assign_suspiciousness(self):
        raise NotImplementedError()

    @staticmethod
    def handle(event, events: List[Type]):
        return any(map(lambda e: isinstance(event, e), events))

    @staticmethod
    @abstractmethod
    def events() -> List[Type]:
        raise NotImplementedError()

    def __gt__(self, other):
        if hasattr(other, "suspiciousness"):
            return self.suspiciousness > other.suspiciousness
        elif isinstance(other, (int, float)):
            return self.suspiciousness > other
        else:
            raise TypeError(f"> supported between {type(self)} and {type(other)}")

    def __lt__(self, other):
        if hasattr(other, "suspiciousness"):
            return self.suspiciousness < other.suspiciousness
        elif isinstance(other, (int, float)):
            return self.suspiciousness < other
        else:
            raise TypeError(f"< supported between {type(self)} and {type(other)}")

    def __ge__(self, other):
        if hasattr(other, "suspiciousness"):
            return self.suspiciousness >= other.suspiciousness
        elif isinstance(other, (int, float)):
            return self.suspiciousness >= other
        else:
            raise TypeError(f">= supported between {type(self)} and {type(other)}")

    def __le__(self, other):
        if hasattr(other, "suspiciousness"):
            return self.suspiciousness <= other.suspiciousness
        elif isinstance(other, (int, float)):
            return self.suspiciousness <= other
        else:
            raise TypeError(f"<= supported between {type(self)} and {type(other)}")
