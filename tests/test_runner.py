import os
from pathlib import Path

from sflkit import Config, instrument_config, Analyzer
from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.suggestion import Location
from sflkit.model import EventFile
from sflkit.runners.run import (
    PytestTree,
    Package,
    Module,
    Function,
    PytestRunner,
    InputRunner,
)
from tests.utils import BaseTest


class RunnerTests(BaseTest):
    PYTEST_COLLECT = (
        "================================================================================================"
        "============================= test session starts =============================================="
        "================================================================================\n"
        "platform darwin -- Python 3.8.4, pytest-7.3.1, pluggy-1.0.0\n"
        "rootdir: /Users/test/test\n"
        "collected 5 items\n\n"
        "<Package tests>\n"
        "  <Module 1.py>\n"
        "    <Function test_1>\n"
        "    <Function test_2>\n"
        "  <Package 1>\n"
        "    <Module 2.py>\n"
        "      <Function test_3>\n"
        "      <Function test_4>\n"
        "    <Module 3.py>\n"
        "      <Function test_5>\n"
        "\n"
        "================================================================================================"
        "=============================== warnings summary ==============================================="
        "================================================================================\n"
        "python3.8/site-packages/future/standard_library/__init__.py:65: DeprecationWarning: "
        "the imp module is deprecated in favour of importlib; see the module's documentation for "
        "alternative uses\n"
        "    import imp\n\n"
        "-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n"
        "================================================================================================"
        "========================== 5 tests collected in 0.05s =========================================="
        "================================================================================\n"
    )

    def test_pytest_tree_parser(self):
        tree = PytestTree()
        tree.parse(self.PYTEST_COLLECT)
        self.assertEqual(1, len(tree.roots))
        package_tests = tree.roots[0]
        self.assertIsInstance(package_tests, Package)
        self.assertEqual(2, len(package_tests.children))
        self.assertEqual("tests", package_tests.name)

        module_1, package_1 = package_tests.children
        self.assertIsInstance(module_1, Module)
        self.assertEqual(2, len(module_1.children))
        self.assertEqual("1.py", module_1.name)

        test_1, test_2 = module_1.children
        self.assertIsInstance(test_1, Function)
        self.assertEqual(0, len(test_1.children))
        self.assertEqual("test_1", test_1.name)
        self.assertIsInstance(test_2, Function)
        self.assertEqual(0, len(test_2.children))
        self.assertEqual("test_2", test_2.name)

        self.assertIsInstance(package_1, Package)
        self.assertEqual(2, len(package_1.children))
        self.assertEqual("1", package_1.name)

        module_2, module_3 = package_1.children
        self.assertIsInstance(module_2, Module)
        self.assertEqual(2, len(module_2.children))
        self.assertEqual("2.py", module_2.name)

        test_3, test_4 = module_2.children
        self.assertIsInstance(test_3, Function)
        self.assertEqual(0, len(test_3.children))
        self.assertEqual("test_3", test_3.name)
        self.assertIsInstance(test_4, Function)
        self.assertEqual(0, len(test_4.children))
        self.assertEqual("test_4", test_4.name)

        self.assertIsInstance(module_3, Module)
        self.assertEqual(1, len(module_3.children))
        self.assertEqual("3.py", module_3.name)

        test_5 = module_3.children[0]
        self.assertIsInstance(test_5, Function)
        self.assertEqual(0, len(test_5.children))
        self.assertEqual("test_5", test_5.name)

    def test_pytest_tree_visit(self):
        tree = PytestTree()
        tree.parse(self.PYTEST_COLLECT)
        tests = list(map(str, tree.visit()))
        expected = [
            "tests/1.py::test_1",
            "tests/1.py::test_2",
            "tests/1/2.py::test_3",
            "tests/1/2.py::test_4",
            "tests/1/3.py::test_5",
        ]
        self.assertEqual(expected, tests)

    def assertPathExists(self, path: os.PathLike):
        self.assertTrue(os.path.exists(path), f"{path} does not exists.")

    def test_runner(self):
        config = Config.create(
            path=os.path.join(self.TEST_RESOURCES, BaseTest.TEST_RUNNER),
            language="python",
            events="line",
            predicates="line",
            working=BaseTest.TEST_DIR,
            exclude="tests",
        )
        instrument_config(config)
        runner = PytestRunner()
        output = Path(BaseTest.TEST_DIR, "events").absolute()
        runner.run(Path(BaseTest.TEST_DIR), output)
        self.assertPathExists(output)
        self.assertPathExists(output / "passing")
        self.assertPathExists(output / "failing")
        self.assertPathExists(output / "undefined")
        analyzer = Analyzer(
            [
                EventFile(
                    output / "failing" / os.listdir(output / "failing")[0],
                    0,
                    failing=True,
                )
            ],
            [
                EventFile(output / "passing" / path, run_id)
                for run_id, path in enumerate(os.listdir(output / "passing"), start=1)
            ],
            config.factory,
        )
        analyzer.analyze()
        predicates = analyzer.get_analysis_by_type(AnalysisType.LINE)
        suggestions = sorted(map(lambda p: p.get_suggestion(), predicates))
        self.assertEqual(1, suggestions[-1].suspiciousness)
        self.assertEqual(1, len(suggestions[-1].lines))
        self.assertEqual(Location("middle.py", 7), suggestions[-1].lines[0])

    def test_input_runner(self):
        config = Config.create(
            path=os.path.join(self.TEST_RESOURCES, BaseTest.TEST_SUGGESTIONS),
            language="python",
            events="line",
            predicates="line",
            working=BaseTest.TEST_DIR,
            exclude="tests",
        )
        instrument_config(config)
        runner = InputRunner(
            "main.py",
            failing=[["2", "1", "3"]],
            passing=[["3", "2", "1"], ["3", "1", "2"]],
        )
        output = Path(BaseTest.TEST_DIR, "events").absolute()
        runner.run(Path(BaseTest.TEST_DIR), output)
        self.assertPathExists(output)
        self.assertPathExists(output / "passing")
        self.assertPathExists(output / "failing")
        self.assertPathExists(output / "undefined")
        analyzer = Analyzer(
            [
                EventFile(
                    output / "failing" / os.listdir(output / "failing")[0],
                    0,
                    failing=True,
                )
            ],
            [
                EventFile(output / "passing" / path, run_id)
                for run_id, path in enumerate(os.listdir(output / "passing"), start=1)
            ],
            config.factory,
        )
        analyzer.analyze()
        predicates = analyzer.get_analysis_by_type(AnalysisType.LINE)
        suggestions = sorted(map(lambda p: p.get_suggestion(), predicates))
        self.assertEqual(1, suggestions[-1].suspiciousness)
        self.assertEqual(1, len(suggestions[-1].lines))
        self.assertEqual(Location("main.py", 10), suggestions[-1].lines[0])
