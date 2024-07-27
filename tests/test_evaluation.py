import random
from typing import Optional

from sflkit.analysis.suggestion import Suggestion, Location
from sflkit.evaluation import Rank, Scenario
from utils import BaseTest


class TestEvaluation(BaseTest):
    def setUp(self):
        random.seed(0)
        self.suggestions = [
            Suggestion([Location("a.py", 1)], 0.5),
            Suggestion([Location("a.py", 2)], 0.3),
            Suggestion([Location("a.py", 3)], 0.7),
            Suggestion([Location("a.py", 4)], 0.1),
            Suggestion([Location("a.py", 5)], 0.9),
            Suggestion([Location("a.py", 6)], 0.2),
            Suggestion([Location("a.py", 7)], 0.8),
            Suggestion([Location("a.py", 8)], 0.4),
            Suggestion([Location("a.py", 9)], 0.6),
            Suggestion([Location("a.py", 10)], 0.0),
        ]

    def get_rank(self, multi: bool = False):
        suggestions = (
            self.suggestions
            if not multi
            else self.suggestions
            + [
                Suggestion(
                    [Location("a.py", 11), Location("a.py", 12), Location("a.py", 13)],
                    0.55,
                )
            ]
        )
        return (
            Rank(suggestions),
            {
                Location("a.py", 2),
                Location("a.py", 6),
                Location("a.py", 7),
                Location("a.py", 8),
            },
        )

    def get_top_n(
        self, n: int, scenario: Optional[Scenario] = None, multi: bool = False
    ):
        rank, locations = self.get_rank(multi=multi)
        return rank.top_n(
            locations,
            n,
            scenario=scenario,
            repeat=10000,
        )

    def get_exam(self, scenario: Optional[Scenario] = None):
        rank, locations = self.get_rank(multi=True)
        return rank.exam(
            locations,
            scenario=scenario,
        )

    def get_wasted_effort(self, scenario: Optional[Scenario] = None):
        rank, locations = self.get_rank(multi=True)
        return rank.wasted_effort(
            locations,
            scenario=scenario,
        )

    def test_top_1(self):
        top_1 = self.get_top_n(1)
        self.assertAlmostEqual(0, top_1, delta=self.DELTA)

    def test_top_5(self):
        top_5 = self.get_top_n(5)
        self.assertAlmostEqual(0.2, top_5, delta=self.DELTA)

    def test_top_10(self):
        top_10 = self.get_top_n(10)
        self.assertAlmostEqual(0.4, top_10, delta=self.DELTA)

    def test_top_5_multi(self):
        top_5_multi = self.get_top_n(5, multi=True)
        self.assertAlmostEqual(0.14285, top_5_multi, delta=0.05)

    def test_top_1_avg(self):
        top_1_avg = self.get_top_n(1, scenario=Scenario.AVG_CASE)
        self.assertAlmostEqual(0, top_1_avg, delta=self.DELTA)

    def test_top_5_avg(self):
        top_5_avg = self.get_top_n(5, scenario=Scenario.AVG_CASE)
        self.assertAlmostEqual(0.5, top_5_avg, delta=self.DELTA)

    def test_top_10_avg(self):
        top_10_avg = self.get_top_n(10, scenario=Scenario.AVG_CASE)
        self.assertAlmostEqual(1, top_10_avg, delta=self.DELTA)

    def test_top_5_avg_multi(self):
        top_5_avg_multi = self.get_top_n(5, scenario=Scenario.AVG_CASE, multi=True)
        self.assertAlmostEqual(0.35714, top_5_avg_multi, delta=0.005)

    def test_top_1_best(self):
        top_1_best = self.get_top_n(1, scenario=Scenario.BEST_CASE)
        self.assertAlmostEqual(0, top_1_best, delta=self.DELTA)

    def test_top_5_best(self):
        top_5_best = self.get_top_n(5, scenario=Scenario.BEST_CASE)
        self.assertAlmostEqual(1, top_5_best, delta=self.DELTA)

    def test_top_10_best(self):
        top_10_best = self.get_top_n(10, scenario=Scenario.BEST_CASE)
        self.assertAlmostEqual(1, top_10_best, delta=self.DELTA)

    def test_top_5_best_multi(self):
        top_5_best_multi = self.get_top_n(5, scenario=Scenario.BEST_CASE, multi=True)
        self.assertAlmostEqual(0.71429, top_5_best_multi, delta=0.005)

    def test_top_1_worst(self):
        top_1_worst = self.get_top_n(1, scenario=Scenario.WORST_CASE)
        self.assertAlmostEqual(0, top_1_worst, delta=self.DELTA)

    def test_top_5_worst(self):
        top_5_worst = self.get_top_n(5, scenario=Scenario.WORST_CASE)
        self.assertAlmostEqual(0.25, top_5_worst, delta=self.DELTA)

    def test_top_10_worst(self):
        top_10_worst = self.get_top_n(10, scenario=Scenario.WORST_CASE)
        self.assertAlmostEqual(1, top_10_worst, delta=self.DELTA)

    def test_top_5_worst_multi(self):
        top_5_worst_multi = self.get_top_n(5, scenario=Scenario.WORST_CASE, multi=True)
        self.assertAlmostEqual(0.17857, top_5_worst_multi, delta=0.005)

    def test_exam_avg(self):
        exam_avg = self.get_exam(scenario=Scenario.AVG_CASE)
        self.assertAlmostEqual(9 / 13, exam_avg, delta=self.DELTA)

    def test_exam_best(self):
        exam_best = self.get_exam(scenario=Scenario.BEST_CASE)
        self.assertAlmostEqual(2 / 13, exam_best, delta=self.DELTA)

    def test_exam_worst(self):
        exam_worst = self.get_exam(scenario=Scenario.WORST_CASE)
        self.assertAlmostEqual(11 / 13, exam_worst, delta=self.DELTA)

    def test_exam(self):
        exam = self.get_exam()
        self.assertAlmostEqual((2 + 9 + 10 + 11) / (13 * 4), exam, delta=self.DELTA)

    def test_wasted_effort_avg(self):
        wasted_effort_avg = self.get_wasted_effort(scenario=Scenario.AVG_CASE)
        self.assertAlmostEqual(9, wasted_effort_avg, delta=self.DELTA)

    def test_wasted_effort_best(self):
        wasted_effort_best = self.get_wasted_effort(scenario=Scenario.BEST_CASE)
        self.assertAlmostEqual(2, wasted_effort_best, delta=self.DELTA)

    def test_wasted_effort_worst(self):
        wasted_effort_worst = self.get_wasted_effort(scenario=Scenario.WORST_CASE)
        self.assertAlmostEqual(11, wasted_effort_worst, delta=self.DELTA)

    def test_wasted_effort(self):
        wasted_effort = self.get_wasted_effort()
        self.assertAlmostEqual((2 + 9 + 10 + 11) / 4, wasted_effort, delta=self.DELTA)
