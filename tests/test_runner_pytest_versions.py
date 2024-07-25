import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from sflkit import Config, instrument_config, Analyzer
from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.suggestion import Location
from sflkit.mapping import EventMapping
from sflkit.model import EventFile
from sflkit.runners.run import (
    PytestRunner,
)
from tests.utils import BaseTest


@unittest.skip
class RunnerTests(BaseTest):
    VENV = Path("test_venv")
    PYTHON_BASE = os.path.join(
        os.path.expanduser("~"), ".pyenv", "versions", "3.8.4", "bin", "python3"
    )
    PYTHON = "python3"

    def assertPathExists(self, path: os.PathLike):
        self.assertTrue(os.path.exists(path), f"{path} does not exists.")

    def create_venv(self, environ):
        shutil.rmtree(self.VENV, ignore_errors=True)
        subprocess.check_call([self.PYTHON_BASE, "-m", "venv", self.VENV], env=environ)

    def activate_venv(self, environ):
        environ["VIRTUAL_ENV"] = str(self.VENV.absolute())
        environ["_OLD_VIRTUAL_PATH"] = environ["PATH"]
        if sys.platform.startswith("win"):
            environ["PATH"] = f'{(self.VENV / "Scripts").absolute()};{environ["PATH"]}'
        else:
            environ["PATH"] = f'{(self.VENV / "bin").absolute()}:{environ["PATH"]}'
        if "PYTHONHOME" in environ:
            environ["_OLD_VIRTUAL_PYTHONHOME"] = environ["PYTHONHOME"]
            del environ["PYTHONHOME"]
        if "VIRTUAL_ENV_DISABLE_PROMPT" not in environ:
            environ["_OLD_VIRTUAL_PS1"] = environ["PS1"] if "PS1" in environ else ""
            environ[
                "PS1"
            ] = f'({self.VENV}) {environ["PS1"] if "PS1" in environ else ""}'
            environ["VIRTUAL_ENV_PROMPT"] = f"({self.VENV})"
        return environ

    def install_pytest(self, environ, pytest_version):
        subprocess.check_call(
            [self.PYTHON, "-m", "pip", "install", f"pytest=={pytest_version}"],
            env=environ,
        )
        subprocess.check_call(
            [self.PYTHON, "-m", "pip", "install", f"sflkitlib"],
            env=environ,
        )

    def tearDown(self):
        shutil.rmtree(self.VENV, ignore_errors=True)

    def _runner_test(self, pytest_version):
        environ = os.environ.copy()
        self.create_venv(environ)
        environ = self.activate_venv(environ)
        self.install_pytest(environ, pytest_version)
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
            Path(BaseTest.TEST_DIR),
            output,
            files=[Path("tests", "test_middle.py")],
            environ=environ,
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

    def test_pytest_3_10_1(self):
        self._runner_test("3.10.1")

    def test_pytest_5_4_3(self):
        self._runner_test("5.4.3")

    def test_pytest_7_0_1(self):
        self._runner_test("7.0.1")
