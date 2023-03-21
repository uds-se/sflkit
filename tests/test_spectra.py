from parameterized import parameterized

from sflkit.analysis import similarity
from sflkit.analysis.spectra import Line
from utils import BaseTest


class TestSimilarityCoefficient(BaseTest):
    @classmethod
    def setUpClass(cls) -> None:
        analysis = cls.run_analysis(
            cls.TEST_SUGGESTIONS,
            "line",
            "line",
            relevant=[["2", "1", "3"]],
            irrelevant=[["3", "2", "1"], ["3", "1", "2"], ["2", "2", "3"]],
        ).get_analysis()
        line = None
        for a in analysis:
            if isinstance(a, Line) and a.file == cls.ACCESS and a.line == 10:
                line = a
                break
        assert line is not None
        cls.line = line
        cls.delta = 0.00001
        cls.expected_results = {
            "AMPLE": 0.6666666666666667,
            "AMPLE2": 0.6666666666666667,
            "Anderberg": 0.3333333333333333,
            "ArithmeticMean": 0.3333333333333333,
            "CBIInc": 0.25,
            "Cohen": 0.5,
            "Crosstab": 1.3333333333333333,
            "Dice": 1,
            "Euclid": 1.7320508075688772,
            "Fleiss": 0.875,
            "Goodman": 0.3333333333333333,
            "Hamann": 0.5,
            "HammingEtc": 3,
            "HarmonicMean": 1.1666666666666667,
            "Jaccard": 0.5,
            "Kulczynski2": 0.75,
            "M1": 3,
            "M2": 0.2,
            "Naish1": 2,
            "Naish2": 0.75,
            "Ochiai": 0.7071067811865475,
            "Ochiai2": 0.5773502691896258,
            "PairScoring": 5,
            "qe": 0.5,
            "RogersAndTanimoto": 0.6,
            "Rogot1": 0.3666666666666667,
            "Rogot2": 0.7916666666666666,
            "RusselAndRao": 0.25,
            "Scott": 0.4666666666666667,
            "SimpleMatching": 0.75,
            "Sokal": 0.8571428571428571,
            "SorensenDice": 0.6666666666666667,
            "Tarantula": 0.75,
            "Wong2": 0,
            "Wong3": 0,
            "Zoltar": 0.5,
        }

    @parameterized.expand(similarity.similarity_coefficients)
    def test_coefficient(self, metric):

        result = getattr(self.line, metric)()

        self.assertAlmostEqual(
            self.expected_results.get(metric, 1),
            result,
            msg=f"The results for {metric} are not correct",
            delta=self.delta,
        )

        self.assertAlmostEqual(
            result,
            getattr(similarity, metric)(
                self.line.passed_observed,
                self.line.passed_not_observed,
                self.line.failed_observed,
                self.line.failed_not_observed,
            ),
            msg=f"The results for {metric} do not match",
            delta=self.delta,
        )
