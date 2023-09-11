import abc
import enum
import hashlib
import os
import re
import shutil
import string
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple

Environment = Dict[str, str]

PYTEST_RESULT_PATTERN = re.compile(
    rb"= ((((?P<f>\d+) failed)|((?P<p>\d+) passed)|(\d+ warnings?))(, )?)+ in "
)

DEFAULT_TIMEOUT = 10


class TestResult(enum.Enum):
    PASSING = "PASSING"
    FAILING = "FAILING"
    UNDEFINED = "UNDEFINED"

    def get_dir(self):
        return self.value.lower()


class Runner(abc.ABC):
    def __init__(self, re_filter: str = r".*", timeout=DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.re_filter = re.compile(re_filter)

    def get_tests(
        self,
        directory: Path,
        files: Optional[List[os.PathLike] | os.PathLike] = None,
        base: Optional[os.PathLike] = None,
        environ: Environment = None,
    ) -> List[str]:
        return []

    def run_test(
        self, directory: Path, test: str, environ: Environment = None
    ) -> TestResult:
        return TestResult.UNDEFINED

    def filter_tests(self, tests: List[str]) -> List[str]:
        return list(filter(self.re_filter.search, tests))

    @staticmethod
    def safe(s: str):
        s = s.encode("ascii", "ignore")
        if len(s) > 255:
            return hashlib.md5(s).hexdigest()
        s = s.decode("ascii")
        for c in string.punctuation:
            if c in s:
                s = s.replace(c, "_")
        return s

    def run_tests(
        self,
        directory: Path,
        output: Path,
        tests: List[str],
        environ: Environment = None,
    ):
        output.mkdir(parents=True, exist_ok=True)
        for test_result in TestResult:
            (output / test_result.get_dir()).mkdir(parents=True, exist_ok=True)
        for run_id, test in enumerate(tests):
            test_result = self.run_test(directory, test, environ=environ)
            if os.path.exists(directory / "EVENTS_PATH"):
                shutil.move(
                    directory / "EVENTS_PATH",
                    output / test_result.get_dir() / self.safe(test),
                )

    def run(
        self,
        directory: Path,
        output: Path,
        files: Optional[List[os.PathLike] | os.PathLike] = None,
        base: Optional[os.PathLike] = None,
        environ: Environment = None,
    ):
        self.run_tests(
            directory,
            output,
            self.filter_tests(
                self.get_tests(directory, files=files, base=base, environ=environ)
            ),
            environ=environ,
        )


class VoidRunner(Runner):
    pass


class PytestRunner(Runner):
    @staticmethod
    def _common_base(directory: Path, tests: List[str]) -> Path:
        parts = directory.parts
        common_bases = {Path(*parts[:i]) for i in range(1, len(parts) + 1)}
        leaves_paths = {Path(r.split("::")[0]) for r in tests}
        common_bases = set(
            filter(
                lambda p: all(map(lambda r: Path(p, *r.parts).exists(), leaves_paths)),
                common_bases,
            )
        )
        for cb in common_bases:
            return cb
        else:
            return None

    def _normalize_paths(
        self,
        tests: List[str],
        directory: Optional[Path] = None,
        root_dir: Optional[Path] = None,
    ):
        result = tests
        if directory:
            base = self._common_base(directory, tests)
            if base is None and root_dir:
                base = self._common_base(root_dir, tests)
            if base is not None:
                result = []
                for r in tests:
                    path, test = r.split("::", 1)
                    result.append(
                        str((base / path).relative_to(directory)) + "::" + test
                    )
        return result

    def get_tests(
        self,
        directory: Path,
        files: Optional[List[os.PathLike] | os.PathLike] = None,
        base: Optional[os.PathLike] = None,
        environ: Environment = None,
    ) -> List[str]:
        c = []
        directory = directory.absolute()
        if files:
            if isinstance(files, (str, os.PathLike)):
                c.append(files)
            else:
                c += files
        if base:
            if not files:
                c.append(base)
            root_dir = directory / base
        else:
            root_dir = directory
        output = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q"] + c,
            stdout=subprocess.PIPE,
            env=environ,
            cwd=directory,
        ).stdout.decode("utf-8")
        tests = output.split("\n\n", 1)[0].split("\n")
        if tests[-1] == "":
            tests = tests[:-1]
        return self._normalize_paths(tests, directory, root_dir)

    @staticmethod
    def __get_pytest_result__(
        output: bytes,
    ) -> tuple[bool, Optional[int], Optional[int]]:
        match = PYTEST_RESULT_PATTERN.search(output)
        if match:
            if match.group("f"):
                failing = int(match.group("f"))
            else:
                failing = 0
            if match.group("p"):
                passing = int(match.group("p"))
            else:
                passing = 0
            return True, passing, failing
        return False, None, None

    def run_test(
        self, directory: Path, test: str, environ: Environment = None
    ) -> TestResult:
        try:
            output = subprocess.run(
                ["python", "-m", "pytest", test],
                stdout=subprocess.PIPE,
                env=environ,
                cwd=directory,
                timeout=self.timeout,
            ).stdout
        except subprocess.TimeoutExpired:
            return TestResult.UNDEFINED
        successful, passing, failing = self.__get_pytest_result__(output)
        if successful:
            if passing > 0 and failing == 0:
                return TestResult.PASSING
            elif failing > 0 and passing == 0:
                return TestResult.FAILING
            else:
                return TestResult.UNDEFINED
        else:
            return TestResult.UNDEFINED


class UnittestRunner(Runner):
    pass


class InputRunner(Runner):
    def __init__(
        self,
        access: os.PathLike,
        passing: List[str | List[str]],
        failing: List[str | List[str]],
    ):
        super().__init__()
        self.access = access
        self.passing: Dict[str, List[str]] = self._prepare_tests(passing, "passing")
        self.failing: Dict[str, List[str]] = self._prepare_tests(failing, "failing")
        self.output: Dict[str, Tuple[str, str]] = dict()

    @staticmethod
    def split(s: str, sep: str = ",", esc: str = "\"'"):
        values = list()
        current = ""
        escape = None
        for c in s:
            if c == escape:
                escape = None
            elif escape is None and c in esc:
                escape = c
            elif escape is None and c in sep:
                values.append(current)
                current = ""
                continue
            current += c
        values.append(current)
        return values

    def _prepare_tests(self, tests: List[str | List[str]], prefix: str):
        return {
            f"{prefix}_{i}": (test if isinstance(test, list) else self.split("\n"))
            for i, test in enumerate(tests)
        }

    def get_tests(
        self,
        directory: Path,
        files: Optional[List[os.PathLike] | os.PathLike] = None,
        base: Optional[os.PathLike] = None,
        environ: Environment = None,
    ) -> List[str]:
        return list(self.passing.keys()) + list(self.failing.keys())

    def run_test(
        self, directory: Path, test_name: str, environ: Environment = None
    ) -> TestResult:
        if "passing" in test_name:
            test = self.passing[test_name]
            result = TestResult.PASSING
        else:
            test = self.failing[test_name]
            result = TestResult.FAILING
        try:
            process = subprocess.run(
                ["python", self.access] + test,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environ,
                cwd=directory,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return TestResult.UNDEFINED
        self.output[test_name] = (
            process.stdout.decode("utf8"),
            process.stderr.decode("utf8"),
        )
        return result
