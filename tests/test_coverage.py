from typing import List

from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.spectra import Line
from utils import BaseTest


class TestCoverage(BaseTest):
    def test_coverage(self):
        analyzer = self.run_analysis(
            self.TEST_SUGGESTIONS,
            "line",
            "line",
            relevant=[["2", "1", "3"]],
            irrelevant=[["3", "2", "1"], ["3", "1", "2"]],
        )
        coverage: List[Line] = analyzer.get_coverage(AnalysisType.LINE)
        coverage = {line.line for line in coverage}
        self.assertEqual(coverage, {1, 5, 6, 7, 9, 10, 12, 13, 16, 19, 20})
