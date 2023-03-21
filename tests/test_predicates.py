from sflkit.analysis.predicate import Condition, Branch
from sflkit.analysis.spectra import Line, Spectrum
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
