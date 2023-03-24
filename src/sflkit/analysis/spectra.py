import math
from abc import ABC
from typing import Callable, Optional

import numpy

from sflkit.analysis.analysis_type import AnalysisObject, AnalysisType
from sflkit.analysis.suggestion import Suggestion, Location
from sflkit.events import EventType
from sflkit.events.event import (
    LineEvent,
    FunctionEnterEvent,
    LoopEndEvent,
    LoopBeginEvent,
    LoopHitEvent,
    DefEvent,
    UseEvent,
)
from sflkit.model.scope import Scope


class Spectrum(AnalysisObject, ABC):
    def __init__(
        self,
        file: str,
        line: int,
        passed_observed: int = 0,
        passed_not_observed: int = 0,
        failed_observed: int = 0,
        failed_not_observed: int = 0,
    ):
        super().__init__(None)
        self.file = file
        self.line = line
        self.passed = passed_observed + passed_not_observed
        self.passed_observed = passed_observed
        self.passed_not_observed = passed_not_observed
        self.failed = failed_observed + failed_not_observed
        self.failed_observed = failed_observed
        self.failed_not_observed = failed_not_observed
        self.hits = dict()

    def get_metric(self, metric: Callable = None):
        if metric is None:
            metric = Spectrum.Ochiai
        try:
            m = metric(self)
            if m == math.nan:
                m = 0
            return m
        except ZeroDivisionError:
            return 0

    def get_suggestion(self, metric: Callable = None, base_dir: str = ""):
        self.assign_suspiciousness(metric)
        return Suggestion([Location(self.file, self.line)], self.suspiciousness)

    def assign_suspiciousness(self, metric: Callable = None):
        self.suspiciousness = self.get_metric(metric)

    def hit(self, id_, event, scope_: Scope = None):
        if id_ not in self.hits:
            self.hits[id_] = 1
        else:
            self.hits[id_] += 1

    def pass_observed(self):
        self.passed_observed += 1

    def fail_observed(self):
        self.failed_observed += 1

    def set_passed(self, passed: int):
        self.passed = passed
        self.passed_not_observed = passed - self.passed_observed

    def set_failed(self, failed: int):
        self.failed = failed
        self.failed_not_observed = failed - self.failed_observed

    def finalize(self, passed: list, failed: list):
        for event_file in failed:
            if event_file in self.hits and self.hits[event_file] > 0:
                self.fail_observed()
        for event_file in passed:
            if event_file in self.hits and self.hits[event_file] > 0:
                self.pass_observed()
        self.set_passed(len(passed))
        self.set_failed(len(failed))

    def AMPLE(self):
        return abs(
            self.failed_observed / self.failed - self.passed_observed / self.passed
        )

    def AMPLE2(self):
        return self.failed_observed / self.failed - self.passed_observed / self.passed

    def Anderberg(self):
        return self.failed_observed / (
            self.failed_observed + 2 * (self.failed_not_observed + self.passed_observed)
        )

    def ArithmeticMean(self):
        return (
            2 * self.failed_observed * self.passed_not_observed
            - 2 * self.failed_not_observed * self.passed_observed
        ) / (
            (self.failed_observed + self.passed_observed)
            * (self.failed_not_observed + self.passed_not_observed)
            * self.failed
            * self.passed
        )

    def Binary(self):
        return 0 if self.failed_observed < self.failed else 1

    def CBIInc(self):
        return self.failed_observed / (
            self.failed_observed + self.passed_observed
        ) - self.failed / (self.failed + self.passed)

    def Cohen(self):
        return (
            2 * self.failed_observed * self.passed_not_observed
            - 2 * self.failed_not_observed * self.passed_observed
        ) / (
            (self.failed_observed + self.passed_observed) * self.passed
            + self.failed * (self.failed_not_observed + self.passed_not_observed)
        )

    def Crosstab(self):
        return (
            (
                self.failed_not_observed
                - (
                    (self.failed_observed + self.passed_observed)
                    * self.failed
                    / (self.failed + self.passed)
                )
            )
            ** 2
            / (
                (self.failed_observed + self.passed_observed)
                * self.failed
                / (self.failed + self.passed)
            )
            + (
                self.passed_observed
                - (
                    (self.failed_observed + self.passed_observed)
                    * self.passed
                    / (self.failed + self.passed)
                )
            )
            ** 2
            / (
                (self.failed_observed + self.passed_observed)
                * self.passed
                / (self.failed + self.passed)
            )
            + (
                self.failed_not_observed
                - (
                    (self.failed_not_observed + self.passed_not_observed)
                    * self.failed
                    / (self.failed + self.passed)
                )
            )
            ** 2
            / (
                (self.failed_not_observed + self.passed_not_observed)
                * self.failed
                / (self.failed + self.passed)
            )
            + (
                self.passed_not_observed
                - (
                    (self.failed_not_observed + self.passed_not_observed)
                    * self.passed
                    / (self.failed + self.passed)
                )
            )
            ** 2
            / (
                (self.failed_not_observed + self.passed_not_observed)
                * self.passed
                / (self.failed + self.passed)
            )
        )

    def Dice(self):
        return 2 * self.failed_observed / (self.failed + self.passed_observed)

    def DStar(self, n=2):
        return (
            self.failed_observed * n / (self.failed_not_observed + self.passed_observed)
        )

    def Euclid(self):
        return numpy.sqrt(self.failed_observed + self.passed_not_observed)

    def Fleiss(self):
        return (
            4 * self.failed_observed * self.passed_not_observed
            - 4 * self.failed_not_observed * self.passed_observed
            - (self.failed_not_observed - self.passed_observed) ** 2
        ) / (
            (2 * self.failed_observed + self.failed_not_observed + self.passed_observed)
            + (
                2 * self.passed_not_observed
                + self.failed_not_observed
                + self.passed_observed
            )
        )

    def GP02(self):
        return 2 * (
            self.failed_observed + numpy.sqrt(self.passed_not_observed)
        ) + numpy.sqrt(self.passed_observed)

    def GP03(self):
        return numpy.sqrt(
            abs(self.failed_observed**2 - numpy.sqrt(self.passed_observed))
        )

    def GP13(self):
        return self.failed_observed * (
            1 + 1 / (2 * self.passed_observed + self.failed_observed)
        )

    def GP19(self):
        return self.failed_observed * numpy.sqrt(
            abs(
                self.passed_observed
                - self.failed_observed
                + self.failed_not_observed
                - self.passed_not_observed
            )
        )

    def Goodman(self):
        return (
            2 * self.failed_observed - self.failed_not_observed - self.passed_observed
        ) / (2 * self.failed_observed + self.failed_not_observed + self.passed_observed)

    def Hamann(self):
        return (
            self.failed_observed
            + self.passed_not_observed
            - self.failed_not_observed
            - self.passed_observed
        ) / (self.failed + self.passed)

    def HammingEtc(self):
        return self.failed_observed + self.passed_not_observed

    def HarmonicMean(self):
        return (
            (
                self.failed_observed * self.passed_not_observed
                - self.failed_not_observed * self.passed_observed
            )
            * (
                (self.failed_observed + self.passed_observed)
                * (self.failed_not_observed + self.passed_not_observed)
                + self.failed * self.passed
            )
            / (
                (self.failed_observed + self.passed_observed)
                * (self.failed_not_observed + self.passed_not_observed)
                * self.failed
                * self.passed
            )
        )

    def Jaccard(self):
        return self.failed_observed / (self.failed + self.passed_observed)

    def Kulczynski1(self):
        return self.failed_observed / (self.failed_not_observed + self.passed_observed)

    def Kulczynski2(self):
        return (
            1
            / 2
            * (
                self.failed_observed / self.failed
                + self.failed_observed / (self.failed_observed + self.passed_observed)
            )
        )

    def M1(self):
        return (self.failed_observed + self.passed_not_observed) / (
            self.failed_not_observed + self.passed_observed
        )

    def M2(self):
        return self.failed_observed / (
            self.failed_observed
            + self.passed_not_observed
            + 2 * (self.failed_not_observed + self.passed_observed)
        )

    def Naish1(self):
        return -1 if self.failed_observed < self.failed else self.passed_not_observed

    def Naish2(self):
        return self.failed_observed - self.passed_observed / (self.passed + 1)

    def Ochiai(self):
        return self.failed_observed / numpy.sqrt(
            self.failed * (self.failed_observed + self.passed_observed)
        )

    def Ochiai2(self):
        return (
            self.failed_observed
            * self.passed_not_observed
            / numpy.sqrt(
                (self.failed_observed + self.passed_observed)
                * (self.failed_not_observed + self.passed_not_observed)
                * self.failed
                * self.passed
            )
        )

    def PairScoring(self):
        return self.failed_observed * (
            2 * self.passed_not_observed + self.passed_observed
        )

    def qe(self):
        return self.failed_observed / (self.failed_observed + self.passed_observed)

    def RogersAndTanimoto(self):
        return (self.failed_observed + self.passed_not_observed) / (
            self.failed_observed
            + self.passed_not_observed
            + 2 * (self.failed_not_observed + self.passed_observed)
        )

    def Rogot1(self):
        return (
            1
            / 2
            * (
                self.failed_observed
                / (
                    2 * self.failed_observed
                    + self.failed_not_observed
                    + self.passed_observed
                )
                + self.passed_not_observed
                / (
                    2 * self.passed_not_observed
                    + self.failed_not_observed
                    + self.passed_observed
                )
            )
        )

    def Rogot2(self):
        return (
            1
            / 4
            * (
                self.failed_observed / (self.failed_observed + self.passed_observed)
                + self.failed_observed / self.failed
                + self.passed_not_observed / self.passed
                + self.passed_not_observed
                / (self.failed_not_observed + self.passed_not_observed)
            )
        )

    def RusselAndRao(self):
        return self.failed_observed / (self.failed + self.passed)

    def Scott(self):
        return (
            4 * self.failed_observed * self.passed_not_observed
            - 4 * self.failed_not_observed * self.passed_observed
            - (self.failed_not_observed - self.passed_observed) ** 2
        ) / (
            (2 * self.failed_observed + self.failed_not_observed + self.passed_observed)
            * (
                2 * self.passed_not_observed
                + self.failed_not_observed
                + self.passed_observed
            )
        )

    def SimpleMatching(self):
        return (self.failed_observed + self.passed_not_observed) / (
            self.failed + self.passed
        )

    def Sokal(self):
        return (
            2
            * (self.failed_observed + self.passed_not_observed)
            / (
                2 * (self.failed_observed + self.passed_not_observed)
                + self.failed_not_observed
                + self.passed_observed
            )
        )

    def SorensenDice(self):
        return (
            2
            * self.failed_observed
            / (
                2 * self.failed_observed
                + self.failed_not_observed
                + self.passed_observed
            )
        )

    def Tarantula(self):
        return (
            self.failed_observed
            / self.failed
            / (self.failed_observed / self.failed + self.passed_observed / self.passed)
        )

    def Wong1(self):
        return self.failed_observed

    def Wong2(self):
        return self.failed_observed - self.passed_observed

    def Wong3(self):
        return self.failed_observed - (
            self.passed_observed
            if self.passed_observed <= 2
            else 2 + 0.1 * (self.passed_observed - 2)
            if self.passed_observed <= 10
            else 2.8 + 0.001 * (self.passed_observed - 10)
        )

    def Zoltar(self):
        return self.failed_observed / (
            self.failed
            + self.passed_observed
            + 10000
            * self.failed_not_observed
            * self.passed_observed
            / self.failed_observed
        )


class Line(Spectrum):
    def __init__(self, event: LineEvent):
        super().__init__(event.file, event.line)

    @staticmethod
    def analysis_type():
        return AnalysisType.LINE

    @staticmethod
    def events():
        return [EventType.LINE]


class Function(Spectrum):
    def __init__(self, event: FunctionEnterEvent):
        super().__init__(event.file, event.line)
        self.function = event.function

    @staticmethod
    def analysis_type():
        return AnalysisType.FUNCTION

    @staticmethod
    def events():
        return [EventType.FUNCTION_ENTER]

    def get_suggestion(self, metric: Callable = None, base_dir: str = ""):
        finder = self.function_finder(self.file, self.line, self.function)
        return Suggestion(
            [Location(self.file, line) for line in finder.get_locations(base_dir)],
            self.get_metric(metric),
        )


class DefUse(Spectrum):
    def __init__(self, def_event: DefEvent, use_event: UseEvent):
        super().__init__(def_event.file, def_event.line)
        self.use_file = use_event.file
        self.use_line = use_event.line
        self.var = def_event.var

    @staticmethod
    def analysis_type():
        return AnalysisType.DEF_USE

    @staticmethod
    def events():
        return [EventType.DEF, EventType.USE]

    def get_suggestion(self, metric: Callable = None, base_dir: str = ""):
        return Suggestion(
            [Location(self.file, self.line), Location(self.use_file, self.use_line)],
            self.get_metric(metric),
        )


class Loop(Spectrum):
    def __init__(
        self,
        event: LoopBeginEvent | LoopHitEvent | LoopEndEvent,
        evaluate_hit: Optional[Callable] = None,
    ):
        super().__init__(event.file, event.line)
        self.loop_stack = list()
        self.evaluate_hit = evaluate_hit if evaluate_hit else self.evaluate_hit_0

    @staticmethod
    def evaluate_hit_0(x):
        return x == 0

    @staticmethod
    def evaluate_hit_1(x):
        return x == 1

    @staticmethod
    def evaluate_hit_more(x):
        return x > 1

    @staticmethod
    def analysis_type():
        return AnalysisType.LOOP

    @staticmethod
    def events():
        return [EventType.LOOP_BEGIN, EventType.LOOP_HIT, EventType.LOOP_END]

    def start_loop(self):
        self.loop_stack.append(0)

    def hit_loop(self):
        self.loop_stack[-1] += 1

    def hit(self, id_, event, scope_: Scope = None):
        hits = self.loop_stack.pop()
        if id_ not in self.hits:
            self.hits[id_] = [hits]
        else:
            self.hits[id_].append(hits)

    def finalize(self, passed: list, failed: list):
        for event_file in failed:
            if event_file in self.hits and any(
                map(self.evaluate_hit, self.hits[event_file])
            ):
                self.fail_observed()
        for event_file in passed:
            if event_file in self.hits and any(
                map(self.evaluate_hit, self.hits[event_file])
            ):
                self.pass_observed()
        self.set_passed(len(passed))
        self.set_failed(len(failed))

    def get_suggestion(self, metric: Callable = None, base_dir: str = ""):
        finder = self.loop_finder(self.file, self.line)
        return Suggestion(
            [Location(self.file, line) for line in finder.get_locations(base_dir)],
            self.get_metric(metric),
        )
