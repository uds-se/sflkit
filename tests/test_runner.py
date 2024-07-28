import os
from pathlib import Path

from sflkit import Config, instrument_config, Analyzer
from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.suggestion import Location
from sflkit.mapping import EventMapping
from sflkit.model import EventFile
from sflkit.runners.run import (
    PytestRunner,
    InputRunner,
    PytestStructure,
)
from tests.utils import BaseTest


class RunnerTests(BaseTest):
    PYTEST_COLLECT = (
        "tests/1.py::test_1\n"
        "tests/1.py::test_2\n"
        "tests/1/2.py::test_3\n"
        "tests/1/2.py::test_4\n"
        "tests/1/3.py::test_5\n"
        "\n"
        "5 tests collected in 0.01s"
    )

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
        runner = PytestRunner(set_python_path=True)
        output = Path(BaseTest.TEST_DIR, "events").absolute()
        runner.run(
            Path(BaseTest.TEST_DIR), output, files=[Path("tests", "test_middle.py")]
        )
        self.assertPathExists(output)
        self.assertPathExists(output / "passing")
        self.assertPathExists(output / "failing")
        self.assertPathExists(output / "undefined")
        mapping = EventMapping.load(config)
        analyzer = Analyzer(
            [
                EventFile(
                    output / "failing" / os.listdir(output / "failing")[0],
                    0,
                    mapping,
                    failing=True,
                )
            ],
            [
                EventFile(output / "passing" / path, run_id, mapping)
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
        mapping = EventMapping.load(config)
        analyzer = Analyzer(
            [
                EventFile(
                    output / "failing" / os.listdir(output / "failing")[0],
                    0,
                    mapping,
                    failing=True,
                )
            ],
            [
                EventFile(output / "passing" / path, run_id, mapping)
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

    def test_parse_and_paths(self):
        collect = (
            "\n"
            "<Package b>\n"
            "  <Module test_b.py>\n"
            "    <Function test_d>\n"
            "<Package tests>\n"
            "  <Module test_a.py>\n"
            "    <Function test_a>\n"
            "    <Function test_b>\n"
            "    <Function test_c>\n"
        )
        tests = PytestStructure.parse_tests(collect)
        self.assertEqual(4, len(tests))
        self.assertIn(os.path.join("b", "test_b.py::test_d"), tests)
        self.assertIn(os.path.join("tests", "test_a.py::test_a"), tests)
        self.assertIn(os.path.join("tests", "test_a.py::test_b"), tests)
        self.assertIn(os.path.join("tests", "test_a.py::test_c"), tests)
        files = PytestRunner.get_files(
            [
                Path("structure", "tests", "b", "test_b.py"),
                Path("structure", "tests", "test_a.py::test_a"),
                Path("structure", "tests", "test_a.py::test_b"),
                Path("structure", "tests", "test_a.py::test_c"),
            ]
        )
        self.assertEqual(2, len(files))
        self.assertIn(os.path.join("structure", "tests", "b", "test_b.py"), files)
        self.assertIn(os.path.join("structure", "tests", "test_a.py"), files)
        directory = Path(BaseTest.TEST_RESOURCES, "structure")
        files = PytestRunner.get_absolute_files(
            files,
            directory,
        )
        self.assertEqual(2, len(files))
        self.assertIn(
            directory / "structure" / "tests" / "b" / "test_b.py",
            files,
        )
        self.assertIn(directory / "structure" / "tests" / "test_a.py", files)
        tests = PytestRunner.normalize_paths(
            tests,
            files=files,
            directory=directory,
            root_dir=directory / "structure" / "tests",
        )
        self.assertEqual(4, len(tests))
        self.assertIn(
            os.path.join("structure", "tests", "b", "test_b.py::test_d"),
            tests,
        )
        self.assertIn(
            os.path.join("structure", "tests", "test_a.py::test_a"),
            tests,
        )
        self.assertIn(
            os.path.join("structure", "tests", "test_a.py::test_b"),
            tests,
        )
        self.assertIn(
            os.path.join("structure", "tests", "test_a.py::test_c"),
            tests,
        )
