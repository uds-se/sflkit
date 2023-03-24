import os

from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.spectra import Spectrum
from sflkit.analysis.suggestion import Location, Suggestion
from utils import BaseTest


class SuggestionsTest(BaseTest):
    def test_location_comparison(self):
        location_1 = Location("main.py", 1)
        location_2 = Location("main.py", 2)
        location_3 = Location("main.py", 1)
        self.assertEqual(location_1, location_3)
        self.assertNotEqual(location_1, location_2)
        self.assertNotEqual(location_2, location_3)
        self.assertEqual(str(location_1), str(location_3))
        self.assertNotEqual(str(location_1), str(location_2))
        self.assertEqual(hash(location_1), hash(location_3))
        self.assertNotEqual(hash(location_1), hash(location_2))

    def test_suggestion_comparison(self):
        suggestion_1 = Suggestion([Location("main.py", 1)], 0.5)
        suggestion_2 = Suggestion([Location("main.py", 2)], 0.3)
        suggestion_3 = Suggestion([Location("main.py", 3)], 0.5)
        self.assertNotEqual(str(suggestion_1), str(suggestion_2))
        self.assertNotEqual(str(suggestion_1), str(suggestion_3))
        self.assertNotEqual(str(suggestion_2), str(suggestion_3))
        self.assertLess(suggestion_2, suggestion_1)
        self.assertLess(suggestion_2, suggestion_3)
        self.assertGreater(suggestion_1, suggestion_2)
        self.assertGreater(suggestion_3, suggestion_2)
        self.assertGreaterEqual(suggestion_1, suggestion_3)
        self.assertLessEqual(suggestion_1, suggestion_3)


class SuggestionsFromPredicatesTest(BaseTest):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = cls.run_analysis(
            cls.TEST_SUGGESTIONS,
            "branch",
            "line,branch,def_use",
            relevant=[["2", "1", "3"]],
            irrelevant=[["3", "2", "1"], ["3", "1", "2"]],
        )
        cls.original_dir = os.path.join(cls.TEST_RESOURCES, cls.TEST_SUGGESTIONS)

    def test_line_suggestions(self):
        predicates = self.analyzer.get_analysis_by_type(AnalysisType.LINE)
        suggestions = sorted(map(lambda p: p.get_suggestion(), predicates))
        self.assertEqual(1, suggestions[-1].suspiciousness)
        self.assertEqual(1, len(suggestions[-1].lines))
        self.assertEqual(Location("main.py", 10), suggestions[-1].lines[0])

    def test_line_sorted_suggestions(self):
        suggestions = self.analyzer.get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.LINE
        )
        self.assertEqual(1, suggestions[0].suspiciousness)
        self.assertEqual(1, len(suggestions[0].lines))
        self.assertEqual(Location("main.py", 10), suggestions[0].lines[0])

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

    def test_sorted_suggestions(self):
        suggestions = self.analyzer.get_sorted_suggestions(base_dir=self.original_dir)
        self.assertEqual(1, suggestions[0].suspiciousness)
        self.assertEqual(3, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 10), suggestions[0].lines)


class SuggestionsFromPredicatesTest2(BaseTest):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = cls.run_analysis(
            cls.TEST_SUGGESTIONS,
            "branch",
            "function,scalar_pair,variable,return",
            relevant=[["2", "1", "3"]],
            irrelevant=[["3", "2", "1"], ["3", "1", "2"]],
        )
        cls.original_dir = os.path.join(cls.TEST_RESOURCES, cls.TEST_SUGGESTIONS)

    def test_function_suggestions(self):
        suggestions = self.analyzer.get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.FUNCTION
        )
        self.assertAlmostEqual(
            0.5773502691896258, suggestions[0].suspiciousness, delta=self.DELTA
        )
        self.assertEqual(13, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 10), suggestions[0].lines)

    def test_scalar_pair_suggestions(self):
        suggestions = self.analyzer.get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.SCALAR_PAIR
        )
        self.assertAlmostEqual(
            0.6666666666666667, suggestions[0].suspiciousness, delta=self.DELTA
        )
        self.assertEqual(2, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 4), suggestions[0].lines)
        self.assertIn(Location("main.py", 5), suggestions[0].lines)

    def test_variable_suggestions(self):
        suggestions = self.analyzer.get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.VARIABLE
        )
        self.assertEqual(0, suggestions[0].suspiciousness)
        self.assertEqual(4, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 4), suggestions[0].lines)
        self.assertIn(Location("main.py", 5), suggestions[0].lines)
        self.assertIn(Location("main.py", 10), suggestions[0].lines)
        self.assertIn(Location("main.py", 13), suggestions[0].lines)

    def test_return_suggestions(self):
        suggestions = self.analyzer.get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.RETURN
        )
        self.assertEqual(0, suggestions[0].suspiciousness)
        self.assertEqual(1, len(suggestions[0].lines))
        self.assertEqual(Location("main.py", 16), suggestions[0].lines[0])


class SuggestionsFromPredicatesTypesTest(BaseTest):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = cls.run_analysis(
            cls.TEST_TYPES,
            "",
            "scalar_pair,return",
            relevant=[["t", ""]],
            irrelevant=[["a", "b"], ["t", "test"], ["test", "t"]],
        )
        cls.original_dir = os.path.join(cls.TEST_RESOURCES, cls.TEST_TYPES)

    def test_scalar_pair_suggestions(self):
        suggestions = self.analyzer.get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.SCALAR_PAIR
        )
        self.assertAlmostEqual(0.75, suggestions[0].suspiciousness, delta=self.DELTA)
        self.assertEqual(1, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 6), suggestions[0].lines)

    def test_return_suggestions(self):
        suggestions = self.analyzer.get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.RETURN
        )
        self.assertAlmostEqual(0.5, suggestions[0].suspiciousness, delta=self.DELTA)
        self.assertEqual(1, len(suggestions[0].lines))
        self.assertEqual(Location("main.py", 13), suggestions[0].lines[0])


class SuggestionsFromPredicatesTest3(BaseTest):
    def _analyze_tests(self, analysis, relevant, irrelevant):

        return self.run_analysis(
            self.TEST_SPECIAL_VALUES,
            "def",
            analysis,
            relevant=[[relevant]],
            irrelevant=[[irrelevant]],
        )

    @classmethod
    def setUpClass(cls):
        cls.original_dir = os.path.join(cls.TEST_RESOURCES, cls.TEST_SPECIAL_VALUES)

    def test_none_suggestions(self):
        suggestions = self._analyze_tests("none", "", "test").get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.NONE
        )
        self.assertAlmostEqual(0.5, suggestions[0].suspiciousness, delta=self.DELTA)
        self.assertEqual(1, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 5), suggestions[0].lines)

    def test_empty_string_suggestions(self):
        suggestions = self._analyze_tests(
            "empty_string", "", "test"
        ).get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.EMPTY_STRING
        )
        self.assertAlmostEqual(0.5, suggestions[0].suspiciousness, delta=self.DELTA)
        self.assertEqual(1, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 3), suggestions[0].lines)

    def test_empty_bytes_suggestions(self):
        suggestions = self._analyze_tests(
            "empty_bytes", "", "test"
        ).get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.EMPTY_BYTES
        )
        self.assertAlmostEqual(0.5, suggestions[0].suspiciousness, delta=self.DELTA)
        self.assertEqual(1, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 4), suggestions[0].lines)

    def test_ascii_string_suggestions(self):
        suggestions = self._analyze_tests(
            "ascii_string", "test", "§"
        ).get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.ASCII_STRING
        )
        self.assertAlmostEqual(0.5, suggestions[0].suspiciousness, delta=self.DELTA)
        self.assertEqual(1, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 3), suggestions[0].lines)

    def test_digit_string_suggestions(self):
        suggestions = self._analyze_tests(
            "digit_string", "123", "test"
        ).get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.DIGIT_STRING
        )
        self.assertAlmostEqual(0.5, suggestions[0].suspiciousness, delta=self.DELTA)
        self.assertEqual(1, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 3), suggestions[0].lines)

    def test_special_string_suggestions(self):
        suggestions = self._analyze_tests(
            "special_string", "§", "test"
        ).get_sorted_suggestions(
            base_dir=self.original_dir, type_=AnalysisType.SPECIAL_STRING
        )
        self.assertAlmostEqual(0.5, suggestions[0].suspiciousness, delta=self.DELTA)
        self.assertEqual(1, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 3), suggestions[0].lines)


class SuggestionsFromPredicatesLoopTest(BaseTest):
    @classmethod
    def setUpClass(cls):
        cls.analyzer = cls.run_analysis(
            cls.TEST_LOOP,
            "",
            "loop",
            relevant=[["00"]],
            irrelevant=[["z"], ["123"]],
        )
        cls.original_dir = os.path.join(cls.TEST_RESOURCES, cls.TEST_LOOP)

    def test_loop_suggestions(self):
        suggestions = self.analyzer.get_sorted_suggestions(
            base_dir=self.original_dir,
            type_=AnalysisType.LOOP,
            metric=Spectrum.Tarantula,
        )
        self.assertAlmostEqual(1, suggestions[0].suspiciousness, delta=self.DELTA)
        self.assertEqual(2, len(suggestions[0].lines))
        self.assertIn(Location("main.py", 7), suggestions[0].lines)
        self.assertIn(Location("main.py", 8), suggestions[0].lines)
