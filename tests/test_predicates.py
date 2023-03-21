import os

from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.predicate import Condition, Branch
from sflkit.analysis.spectra import Line, Spectrum
from sflkit.analysis.suggestion import Location
from utils import BaseTest


class EventTests(BaseTest):
    def test_lines_relevant(self):
        predicates = self.run_analysis(
            self.TEST_LINES, "line", "line", relevant=[[]]
        ).get_analysis()
        line = False
        for p in predicates:
            self.assertIsInstance(p, Line)
            line = True
            self.assertEqual(1, p.qe(), f"qe is wrong for {p}")
        self.assertTrue(line)

    def test_lines_irrelevant(self):
        predicates = self.run_analysis(
            self.TEST_LINES, "line", "line", irrelevant=[[]]
        ).get_analysis()
        line = False
        for p in predicates:
            self.assertIsInstance(p, Line)
            line = True
            self.assertEqual(0, p.qe(), f"qe is wrong for {p}")
        self.assertTrue(line)

    def test_branches_relevant(self):
        predicates = self.run_analysis(
            self.TEST_BRANCHES, "branch", "line,branch,condition", relevant=[[]]
        ).get_analysis()
        line, condition, branch = False, False, False
        for p in predicates:
            if isinstance(p, Line):
                self.assertEqual(1, p.get_metric(Spectrum.qe), f"qe is wrong for {p}")
                line = True
            elif isinstance(p, Condition):
                self.assertEqual(1, p.get_metric(Spectrum.qe), f"qe is wrong for {p}")
                condition = True
            elif isinstance(p, Branch):
                if p.passed_observed or p.failed_observed:
                    self.assertEqual(
                        1, p.get_metric(Spectrum.qe), f"qe is wrong for {p}"
                    )
                    branch = True
                else:
                    self.assertEqual(
                        0, p.get_metric(Spectrum.qe), f"qe is wrong for {p}"
                    )
        self.assertTrue(line and condition and branch)

    def test_branches_irrelevant(self):
        predicates = self.run_analysis(
            self.TEST_BRANCHES, "branch", "line,branch,condition", irrelevant=[[]]
        ).get_analysis()
        line, condition, branch = False, False, False
        for p in predicates:
            if isinstance(p, Line):
                self.assertEqual(p.get_metric(Spectrum.qe), 0, f"qe is wrong for {p}")
                line = True
            elif isinstance(p, Condition):
                self.assertEqual(p.get_metric(Spectrum.qe), 0, f"qe is wrong for {p}")
                condition = True
            elif isinstance(p, Branch):
                self.assertEqual(p.get_metric(Spectrum.qe), 0, f"qe is wrong for {p}")
                branch = True
        self.assertTrue(line and condition and branch)


class SuggestionsTest(BaseTest):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = cls.run_analysis(
            cls.TEST_SUGGESTIONS,
            "branch",
            "line,branch,def_use",
            relevant=[["2", "1", "3"]],
            irrelevant=[["3", "2", "1"], ["3", "1", "2"]],
        )
        cls.original_dir = os.path.join(cls.TEST_RESOURCES, "test_suggestions")

    def test_line_suggestions(self):
        predicates = self.analyzer.get_analysis_by_type(AnalysisType.LINE)
        suggestions = sorted(map(lambda p: p.get_suggestion(), predicates))
        self.assertEqual(1, suggestions[-1].suspiciousness)
        self.assertEqual(1, len(suggestions[-1].lines))
        self.assertEqual(Location("main.py", 10), suggestions[-1].lines[0])

    def test_def_use_suggestions(self):
        predicates = self.analyzer.get_analysis_by_type(AnalysisType.DEF_USE)
        suggestions = sorted(map(lambda p: p.get_suggestion(), predicates))
        self.assertEqual(1, suggestions[-1].suspiciousness)
        self.assertEqual(2, len(suggestions[-1].lines))
        self.assertIn(Location("main.py", 10), suggestions[-1].lines)

    def test_branch_suggestions(self):
        predicates = self.analyzer.get_analysis_by_type(AnalysisType.BRANCH)
        suggestions = sorted(
            map(lambda p: p.get_suggestion(base_dir=self.original_dir), predicates)
        )
        self.assertEqual(0.5, suggestions[-1].suspiciousness)
        self.assertEqual(2, len(suggestions[-1].lines))
        self.assertIn(Location("main.py", 10), suggestions[-1].lines)
