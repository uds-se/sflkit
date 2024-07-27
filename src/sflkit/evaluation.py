import enum
import random
from typing import List, Dict, Callable, Set, Optional

from sflkit.analysis.suggestion import Suggestion, Location


class Average:
    def __init__(self):
        self.number_of_locations = 0

    def average(self, suspiciousness: float, current_suspiciousness: float):
        current_suspiciousness *= self.number_of_locations
        self.number_of_locations += 1
        return (current_suspiciousness + suspiciousness) / self.number_of_locations


class Scenario(enum.Enum):
    BEST_CASE = "best_case"
    AVG_CASE = "avg_case"
    WORST_CASE = "worst_case"


class Rank:
    def __init__(
        self,
        suggestions: List[Suggestion],
        metric: Callable[[float, float], float] = max,
        default_suspiciousness: float = float("-inf"),
    ):
        self.suggestions = sorted(suggestions, reverse=True)
        self.suspiciousness: Dict[Location, float] = dict()
        self.ranks: Dict[float, List[Location]] = dict()
        self.locations: Dict[Location, float] = dict()
        current_rank = 1
        for i, suggestion in enumerate(self.suggestions):
            lines = suggestion.lines
            if len(lines) == 0:
                continue
            elif len(lines) == 1:
                rank = current_rank
                current_rank += 1
            else:
                rank = (len(lines)) / 2 + (current_rank - 1)
                current_rank += len(lines)
            self.ranks[rank] = lines
            for line in lines:
                self.suspiciousness[line] = metric(
                    suggestion.suspiciousness,
                    self.locations.get(line, default_suspiciousness),
                )
                self.locations[line] = rank
        self.number_of_locations = len(self.locations)

    def top_n(
        self,
        faulty: Set[Location],
        n: int,
        scenario: Optional[Scenario] = None,
        repeat: int = 1000,
    ) -> float:
        top_n_locations = list()
        for suggestion in self.suggestions:
            if len(top_n_locations) >= n:
                break
            for line in suggestion.lines:
                if line not in top_n_locations:
                    top_n_locations.append(line)
        if len(top_n_locations) <= n:
            return self._top_n(faulty, top_n_locations, scenario)
        else:
            sum_ = 0
            for _ in range(repeat):
                sum_ += self._top_n(
                    faulty, random.sample(top_n_locations, k=n), scenario
                )
            return sum_ / repeat

    @staticmethod
    def _top_n(
        faulty: Set[Location],
        top_n_locations: List[Location],
        scenario: Optional[Scenario] = None,
    ) -> float:
        found = len(faulty.intersection(top_n_locations))
        if scenario == Scenario.BEST_CASE:
            return 1 if found > 0 else 0
        elif scenario == Scenario.WORST_CASE:
            return found / len(faulty)
        elif scenario == Scenario.AVG_CASE:
            return min(found / (len(faulty) / 2), 1)
        else:
            return found / len(top_n_locations)

    def get_rank(
        self, faulty: Set[Location], scenario: Optional[Scenario] = None
    ) -> float:
        if scenario == Scenario.BEST_CASE:
            rank = min(self.locations[location] for location in faulty)
        elif scenario == Scenario.WORST_CASE:
            rank = max(self.locations[location] for location in faulty)
        elif scenario == Scenario.AVG_CASE:
            rank = sorted([self.locations[location] for location in faulty])[
                max(len(faulty) // 2 - 1, 0)
            ]
        else:
            rank = sum(self.locations[location] for location in faulty) / len(faulty)
        return rank

    def exam(self, faulty: Set[Location], scenario: Optional[Scenario] = None) -> float:
        return self.get_rank(faulty, scenario) / self.number_of_locations

    def wasted_effort(
        self, faulty: Set[Location], scenario: Optional[Scenario] = None
    ) -> float:
        return self.get_rank(faulty, scenario)
