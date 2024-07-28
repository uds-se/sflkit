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

from sflkit.logger import LOGGER

Environment = Dict[str, str]

PYTEST_RESULT_PATTERN = re.compile(
    rb"=( |\x1b\[\d+m)+(("
    rb"((?P<f>\d+) failed)|"
    rb"((?P<p>\d+) passed)|"
    rb"(\d+ (skipped|warning(s?)|deselected|"
    rb"(error(s?)))))"
    rb"(( |\x1b\[\d+m)*,( |\x1b\[\d+m)+)?)+( |\x1b\[\d+m)+in( |\x1b\[\d+m)+"
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
        self.passing_tests = set()
        self.failing_tests = set()
        self.undefined_tests = set()
        self.tests = {
            TestResult.PASSING: self.passing_tests,
            TestResult.FAILING: self.failing_tests,
            TestResult.UNDEFINED: self.undefined_tests,
        }

    def get_tests(
        self,
        directory: Path,
        files: Optional[List[os.PathLike] | os.PathLike] = None,
        base: Optional[os.PathLike] = None,
        environ: Environment = None,
        k: str = None,
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
            self.tests[test_result].add(test)
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
        k: str = None,
    ):
        self.passing_tests.clear()
        self.failing_tests.clear()
        self.undefined_tests.clear()
        self.run_tests(
            directory,
            output,
            self.filter_tests(
                self.get_tests(directory, files=files, base=base, environ=environ, k=k)
            ),
            environ=environ,
        )


class VoidRunner(Runner):
    pass


class PytestStructure:
    def __init__(self, name: str, parent: Optional["PytestStructure"] = None):
        self.name = name
        self.children = []
        self.parent = parent
        self.depth = 0

    def add_child(self, child):
        self.children.append(child)

    def set_parent(self, parent):
        self.parent = parent

    def get_seperator(self):
        return ""

    def get_tests(self) -> List[str]:
        if self.children:
            return [
                self.name + self.get_seperator() + test
                for child in self.children
                for test in child.get_tests()
            ]
        else:
            return [self.name]

    DIR = "Dir"
    PACKAGE = "Package"
    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    UNIT_TEST_CASE = "UnitTestCase"
    TEST_CASE_FUNCTION = "TestCaseFunction"

    @staticmethod
    def get_pattern(obj):
        return re.compile(
            rf"<{obj} "
            r"('(?P<name_single>([^']|\\')*)'"
            r"|\"(?P<name_double>([^\"]|\\\")*)\""
            r"|(?P<name>[^\"'][^>]*))"
            r">"
        )

    @staticmethod
    def clean_line(line: str) -> str:
        return line.replace("\\\\", "\\")

    @staticmethod
    def parse_tests(output: str) -> List[str]:
        trees = []
        current = None
        for original_line in output.split("\n"):
            line = original_line.lstrip()
            level = len(original_line) - len(line)
            if f"<{PytestStructure.DIR}" in line:
                structure = Directory
                pattern = PytestStructure.get_pattern(PytestStructure.DIR)
            elif f"<{PytestStructure.PACKAGE}" in line:
                structure = Directory
                pattern = PytestStructure.get_pattern(PytestStructure.PACKAGE)
            elif f"<{PytestStructure.MODULE}" in line:
                structure = Module
                pattern = PytestStructure.get_pattern(PytestStructure.MODULE)
            elif f"<{PytestStructure.CLASS}" in line:
                structure = Class
                pattern = PytestStructure.get_pattern(PytestStructure.CLASS)
            elif f"<{PytestStructure.FUNCTION}" in line:
                structure = Function
                pattern = PytestStructure.get_pattern(PytestStructure.FUNCTION)
            elif f"<{PytestStructure.UNIT_TEST_CASE}" in line:
                structure = Class
                pattern = PytestStructure.get_pattern(PytestStructure.UNIT_TEST_CASE)
            elif f"<{PytestStructure.TEST_CASE_FUNCTION}" in line:
                structure = Function
                pattern = PytestStructure.get_pattern(
                    PytestStructure.TEST_CASE_FUNCTION
                )
            else:
                continue
            line = PytestStructure.clean_line(line)
            match = pattern.search(line)
            if match:
                name = (
                    match.group("name_single")
                    or match.group("name_double")
                    or match.group("name")
                )
                if match.group("name_single"):
                    name = name.replace("\\'", "'")
                elif match.group("name_double"):
                    name = name.replace('\\"', '"')
                obj = structure(name)
                obj.depth = level
                if current is None:
                    trees.append(obj)
                elif current.depth < obj.depth:
                    obj.set_parent(current)
                    current.add_child(obj)
                elif current.depth >= obj.depth:
                    while current and current.depth >= obj.depth:
                        current = current.parent
                    if current is None:
                        trees.append(obj)
                    else:
                        obj.set_parent(current)
                        current.add_child(obj)
                current = obj
        return [test for tree in trees for test in tree.get_tests()]

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name}>"


class Directory(PytestStructure):
    def get_seperator(self):
        return os.sep


class Module(PytestStructure):
    def get_seperator(self):
        return "::"


class Class(PytestStructure):
    def get_seperator(self):
        return "::"


class Function(PytestStructure):
    def get_seperator(self):
        return "::"


class PytestRunner(Runner):
    def __init__(
        self,
        re_filter: str = r".*",
        timeout=DEFAULT_TIMEOUT,
        set_python_path: bool = False,
    ):
        super().__init__(re_filter, timeout)
        self.set_python_path = set_python_path

    @staticmethod
    def _common_base(directory: Path, tests: List[str]) -> Path:
        parts = directory.parts
        common_bases = {Path(*parts[:i]) for i in range(1, len(parts) + 1)}
        if "::" in tests[0]:
            leaves_paths = {Path(r.split("::")[0]) for r in tests}
        else:
            leaves_paths = {Path(r) for r in tests}
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

    @staticmethod
    def _common_path(files: List[str]) -> Optional[Path]:
        paths = []
        for f in files:
            if "::" in f:
                paths.append(f.split("::")[0])
            else:
                paths.append(f)
        common_path = os.path.commonpath(paths)
        if common_path:
            return Path(common_path)
        return None

    def _normalize_paths(
        self,
        tests: List[str],
        file_base: Optional[Path] = None,
        directory: Optional[Path] = None,
        root_dir: Optional[Path] = None,
    ):
        result = tests
        if directory:
            base = None
            if file_base:
                base = self._common_base(file_base, tests)
            if base is None:
                base = self._common_base(directory, tests)
            if base is None and root_dir:
                base = self._common_base(root_dir, tests)
            if base is None and root_dir is not None:
                result = []
                for r in tests:
                    path, test = r.split("::", 1)
                    result.append(
                        str((root_dir / path).relative_to(directory)) + "::" + test
                    )
            elif base is not None:
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
        k: str = None,
    ) -> List[str]:
        c = []
        directory = directory.absolute()
        if k:
            c.append("-k")
            c.append(k)
        if base:
            if not files:
                c.append(str(base))
            root_dir = directory / base
        else:
            root_dir = directory
        file_base = None
        if files:
            if isinstance(files, (str, os.PathLike)):
                str_files = [str(files)]
            else:
                str_files = [str(f) for f in files]
            common_path = self._common_path(str_files)
            if common_path:
                file_base = root_dir / common_path
            c += str_files
        process = subprocess.run(
            [
                "python3",
                "-m",
                "pytest",
                "--collect-only",
            ]
            + c,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environ,
            cwd=directory,
        )
        LOGGER.info(f"pytest collection finished with {process.returncode}")
        tests = PytestStructure.parse_tests(process.stdout.decode("utf8"))
        return self._normalize_paths(tests, file_base, directory, root_dir)

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
                ["python3", "-m", "pytest", test],
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
        k: str = None,
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
                ["python3", self.access] + test,
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
