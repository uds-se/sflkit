import os
from pathlib import Path

from sflkit import Config, instrument_config, Analyzer
from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.suggestion import Location
from sflkit.model import EventFile
from sflkit.runners.run import (
    PytestRunner,
    InputRunner,
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
        runner = PytestRunner()
        output = Path(BaseTest.TEST_DIR, "events").absolute()
        runner.run(
            Path(BaseTest.TEST_DIR), output, files=[Path("tests", "test_middle.py")]
        )
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
