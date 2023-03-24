import enum
from abc import ABC
from typing import Tuple, Callable, Optional

from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.spectra import Spectrum
from sflkit.analysis.suggestion import Suggestion, Location
from sflkit.events import EventType
from sflkit.events.event import BranchEvent, FunctionExitEvent, DefEvent
from sflkit.model import scope


class Predicate(Spectrum, ABC):
    def __init__(self, file, line):
        super().__init__(file, line)
        self.true_relevant = 0
        self.false_relevant = 0
        self.true_irrelevant = 0
        self.false_irrelevant = 0
        self.fail_true = 0
        self.fail_false = 0
        self.context = 1
        self.increase_true = 0
        self.increase_false = 0
        self.true_hits = dict()

    def finalize(self, passed: list, failed: list):
        super().finalize(passed, failed)
        for p in passed:
            if p in self.true_hits:
                if self.true_hits[p] > 0:
                    self.true_irrelevant_observed()
                else:
                    self.false_irrelevant_observed()
        for f in failed:
            if f in self.true_hits:
                if self.true_hits[f] > 0:
                    self.true_relevant_observed()
                else:
                    self.false_relevant_observed()

    def hit(self, id_, event, scope_: scope.Scope = None):
        super(Predicate, self).hit(id_, event, scope_)
        if id_ not in self.true_hits:
            self.true_hits[id_] = 0
        if self._evaluate_predicate(scope_):
            self.true_hits[id_] += 1

    def get_metric(self, metric: Callable = None):
        if metric is None:
            metric = Predicate.IncreaseTrue
        return super().get_metric(metric)

    def _evaluate_predicate(self, scope_: scope.Scope):
        return False

    def true_relevant_observed(self):
        self.true_relevant += 1

    def true_irrelevant_observed(self):
        self.true_irrelevant += 1

    def false_relevant_observed(self):
        self.false_relevant += 1

    def false_irrelevant_observed(self):
        self.false_irrelevant += 1

    def Fail(self) -> Tuple[float, float]:
        try:
            self.fail_true = self.true_relevant / (
                self.true_relevant + self.true_irrelevant
            )
        except ZeroDivisionError:
            pass
        try:
            self.fail_false = self.false_relevant / (
                self.false_relevant + self.false_irrelevant
            )
        except ZeroDivisionError:
            pass
        return self.fail_true, self.fail_false

    def Contex(self) -> float:
        try:
            self.context = (self.true_relevant + self.false_relevant) / (
                self.true_relevant
                + self.true_irrelevant
                + self.false_relevant
                + self.false_irrelevant
            )
        except ZeroDivisionError:
            pass
        return self.context

    def IncreaseTrue(self) -> float:
        return self.increase_true

    def IncreaseFalse(self) -> float:
        return self.increase_false

    def Increase(self) -> Tuple[float, float]:
        self.increase_true = self.fail_true - self.context
        self.increase_false = self.fail_false - self.context
        return self.increase_true, self.increase_false

    def calculate(self):
        self.Fail()
        self.Contex()
        self.Increase()


class Branch(Predicate):
    def __init__(self, event: BranchEvent, then: bool = True):
        super().__init__(event.file, event.line)
        self.then_id = event.then_id if then else event.else_id
        self.then = then

    @staticmethod
    def analysis_type() -> AnalysisType:
        return AnalysisType.BRANCH

    @staticmethod
    def events():
        return [EventType.BRANCH]

    def hit(self, id_, event, scope_: scope.Scope = None):
        if id_ not in self.true_hits:
            self.true_hits[id_] = 0
        if event.then_id == self.then_id:
            super(Predicate, self).hit(id_, event, scope_)
            self.true_hits[id_] += 1

    def get_suggestion(self, metric: Callable = None, base_dir: str = ""):
        if metric == Predicate.IncreaseFalse:
            finder = self.branch_finder(self.file, self.line, not self.then)
        else:
            finder = self.branch_finder(self.file, self.line, self.then)
        return Suggestion(
            [Location(self.file, line) for line in finder.get_locations(base_dir)],
            self.get_metric(metric),
        )


class Comp(enum.Enum):
    LT = 0
    LE = 1
    EQ = 2
    GE = 3
    GT = 4
    NE = 5

    def evaluate(self, x, y):
        if self == Comp.LT:
            return x < y
        elif self == Comp.LE:
            return x <= y
        elif self == Comp.EQ:
            return x == y
        elif self == Comp.GE:
            return x >= y
        elif self == Comp.GT:
            return x > y
        elif self == Comp.NE:
            return x != y


class Comparison(Predicate, ABC):
    def __init__(self, file, line, op: Comp):
        super().__init__(file, line)
        self.op = op

    @staticmethod
    def events():
        return [
            EventType.DEF,
            EventType.FUNCTION_ENTER,
            EventType.FUNCTION_EXIT,
            EventType.FUNCTION_ERROR,
        ]

    def _evaluate_predicate(self, scope_: scope.Scope) -> bool:
        return self._compare(self._get_first(scope_), self._get_second(scope_))

    def _compare(self, first, second) -> bool:
        return self.op.evaluate(first, second)

    def _get_first(self, scope_: scope.Scope):
        return 0

    def _get_second(self, scope_: scope.Scope):
        return 0


class ScalarPair(Comparison):
    def __init__(self, event, op: Comp, var: str):
        super().__init__(event.file, event.line, op)
        self.var1 = event.var
        self.var2 = var

    @staticmethod
    def analysis_type():
        return AnalysisType.SCALAR_PAIR

    def _get_first(self, scope_: scope.Scope):
        return scope_.value(self.var1)

    def _get_second(self, scope_: scope.Scope):
        return scope_.value(self.var2)


class VariablePredicate(Comparison):
    def __init__(self, event, op: Comp):
        super().__init__(event.file, event.line, op)
        self.var = event.var

    @staticmethod
    def analysis_type():
        return AnalysisType.VARIABLE

    @staticmethod
    def events():
        return [
            EventType.DEF,
        ]

    def _get_first(self, scope_: scope.Scope):
        return scope_.value(self.var)


class NonePredicate(Comparison):
    def __init__(self, event: DefEvent):
        super().__init__(event.file, event.line, Comp.EQ)
        self.var = event.var

    @staticmethod
    def analysis_type():
        return AnalysisType.NONE

    @staticmethod
    def events():
        return [
            EventType.DEF,
        ]

    def _get_first(self, scope_: scope.Scope):
        return scope_.value(self.var)

    def _get_second(self, scope_: scope.Scope):
        return None


class ReturnPredicate(Comparison):
    def __init__(self, event: FunctionExitEvent, op: Comp, value: Optional[int] = 0):
        super().__init__(event.file, event.line, op)
        self.function = event.function
        self.value = value

    @staticmethod
    def analysis_type():
        return AnalysisType.RETURN

    @staticmethod
    def events():
        return [
            EventType.FUNCTION_ENTER,
            EventType.FUNCTION_EXIT,
            EventType.FUNCTION_ERROR,
        ]

    def _get_first(self, scope_: scope.Scope):
        return scope_.value(self.function)

    def _get_second(self, scope_: scope.Scope):
        return self.value


class EmptyStringPredicate(Comparison):
    def __init__(self, event: DefEvent):
        super().__init__(event.file, event.line, Comp.EQ)
        self.var = event.var

    @staticmethod
    def analysis_type():
        return AnalysisType.EMPTY_STRING

    @staticmethod
    def events():
        return [
            EventType.DEF,
        ]

    def _get_first(self, scope_: scope.Scope):
        return scope_.value(self.var)

    def _get_second(self, scope_: scope.Scope):
        return ""


class EmptyBytesPredicate(Comparison):
    def __init__(self, event: DefEvent):
        super().__init__(event.file, event.line, Comp.EQ)
        self.var = event.var

    @staticmethod
    def analysis_type():
        return AnalysisType.EMPTY_BYTES

    @staticmethod
    def events():
        return [
            EventType.DEF,
        ]

    def _get_first(self, scope_: scope.Scope):
        return scope_.value(self.var)

    def _get_second(self, scope_: scope.Scope):
        return b""


class FunctionPredicate(Predicate, ABC):
    def __init__(self, file, line, var: str, predicate: callable):
        super().__init__(file, line)
        self.var = var
        self.predicate = predicate

    @staticmethod
    def events():
        return [
            EventType.DEF,
        ]

    def _evaluate_predicate(self, scope_: scope.Scope):
        value = scope_.value(self.var)
        return isinstance(value, str) and self.predicate(scope_.value(self.var))


class IsAsciiPredicate(FunctionPredicate):
    def __init__(self, event: DefEvent):
        super().__init__(event.file, event.line, event.var, str.isascii)

    @staticmethod
    def analysis_type():
        return AnalysisType.ASCII_STRING


class ContainsDigitPredicate(FunctionPredicate):
    def __init__(self, event: DefEvent):
        super().__init__(event.file, event.line, event.var, self._contains_digit)

    @staticmethod
    def _contains_digit(s):
        return any(c.isdigit() for c in s)

    @staticmethod
    def analysis_type():
        return AnalysisType.DIGIT_STRING


class ContainsSpecialPredicate(FunctionPredicate):
    def __init__(self, event: DefEvent):
        super().__init__(event.file, event.line, event.var, self._contain_special)

    @staticmethod
    def _contain_special(s):
        return not s.isalnum()

    @staticmethod
    def analysis_type():
        return AnalysisType.SPECIAL_STRING


class Condition(Predicate):
    def __init__(self, file: str, line: int, condition: str):
        super().__init__(file, line)
        self.condition = condition

    @staticmethod
    def analysis_type():
        return AnalysisType.CONDITION

    @staticmethod
    def events():
        return [EventType.CONDITION]

    def hit(self, id_, event, scope_: scope.Scope = None):
        super(Predicate, self).hit(id_, event, scope_)
        if id_ not in self.true_hits:
            self.true_hits[id_] = 0
        if event.value:
            self.true_hits[id_] += 1
