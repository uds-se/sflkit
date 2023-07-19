import abc
import enum
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

Environment = Dict[str, str]

PYTEST_COLLECT_PATTERN = re.compile(
    '<(?P<kind>Package|Module|Class|Function|UnitTestCase|TestCaseFunction) (?P<name>[^>]+|"([^"]|\\")+")>'
)
PYTEST_RESULT_PATTERN = re.compile(
    rb"= ((((?P<f>\d+) failed)|((?P<p>\d+) passed)|(\d+ warnings?))(, )?)+ in "
)


class PytestNode(abc.ABC):
    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent: Optional[PytestNode] = parent
        self.children: List[PytestNode] = []

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.__repr__()

    @abc.abstractmethod
    def visit(self) -> List[Any]:
        pass


class Package(PytestNode):
    def visit(self) -> List[Any]:
        return sum([node.visit() for node in self.children], start=[])

    def __repr__(self):
        if self.parent:
            return os.path.join(repr(self.parent), self.name)
        else:
            return self.name


class Module(PytestNode):
    def visit(self) -> List[Any]:
        return sum([node.visit() for node in self.children], start=[])

    def __repr__(self):
        if self.parent:
            return os.path.join(repr(self.parent), self.name)
        else:
            return self.name


class Class(PytestNode):
    def visit(self) -> List[Any]:
        return sum([node.visit() for node in self.children], start=[])

    def __repr__(self):
        if self.parent:
            return f"{repr(self.parent)}::{self.name}"
        else:
            return f"::{self.name}"


class Function(PytestNode):
    def visit(self) -> List[Any]:
        return [self] + sum([node.visit() for node in self.children], start=[])

    def __repr__(self):
        if self.parent:
            return f"{repr(self.parent)}::{self.name}"
        else:
            return f"::{self.name}"


class PytestTree:
    def __init__(self):
        self.roots: List[PytestNode] = []

    @staticmethod
    def _count_spaces(s: str):
        return len(s) - len(s.lstrip())

    def parse(self, output: str, directory: Path = None):
        current_level = 0
        current_node = None
        for line in output.split("\n"):
            match = PYTEST_COLLECT_PATTERN.search(line)
            if match:
                level = self._count_spaces(line) // 2
                name = match.group("name")
                if match.group("kind") == "Package":
                    node_class = Package
                    if directory:
                        name = os.path.relpath(name, directory)
                elif match.group("kind") == "Module":
                    node_class = Module
                    if directory:
                        name = os.path.relpath(name, directory)
                elif match.group("kind") in ("Class", "UnitTestCase"):
                    node_class = Class
                elif match.group("kind") in ("Function", "TestCaseFunction"):
                    node_class = Function
                else:
                    continue
                node = node_class(name)
                if level == 0:
                    current_node = node
                    current_level = 0
                    self.roots.append(node)
                elif level > current_level:
                    current_node.children.append(node)
                    node.parent = current_node
                    current_node = node
                    current_level = level
                else:
                    for _ in range(current_level - level + 1):
                        if current_node.parent:
                            current_node = current_node.parent
                    current_node.children.append(node)
                    node.parent = current_node
                    current_node = node
                    current_level = level

    def visit(self):
        return sum([node.visit() for node in self.roots], start=[])


class TestResult(enum.Enum):
    PASSING = "PASSING"
    FAILING = "FAILING"
    UNDEFINED = "UNDEFINED"

    def get_dir(self):
        return self.value.lower()


class Runner(abc.ABC):
    def __init__(self, re_filter: str = r".*"):
        self.re_filter = re.compile(re_filter)

    def get_tests(self, directory: Path, environ: Environment = None) -> List[str]:
        return []

    def run_test(
        self, directory: Path, test: str, environ: Environment = None
    ) -> TestResult:
        return TestResult.UNDEFINED

    def filter_tests(self, tests: List[str]) -> List[str]:
        return list(filter(self.re_filter.search, tests))

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
                    output / test_result.get_dir() / str(run_id),
                )

    def run(self, directory: Path, output: Path, environ: Environment = None):
        self.run_tests(
            directory,
            output,
            self.filter_tests(self.get_tests(directory, environ=environ)),
            environ=environ,
        )


class VoidRunner(Runner):
    pass


class PytestRunner(Runner):
    def get_tests(self, directory: Path, environ: Environment = None) -> List[str]:
        output = subprocess.run(
            ["python", "-m", "pytest", "--collect-only"],
            stdout=subprocess.PIPE,
            env=environ,
            cwd=directory,
        ).stdout.decode("utf-8")
        tree = PytestTree()
        tree.parse(output, directory=directory)
        return list(map(str, tree.visit()))

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
        output = subprocess.run(
            ["python", "-m", "pytest", test],
            stdout=subprocess.PIPE,
            env=environ,
            cwd=directory,
        ).stdout
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
    def _prepare_tests(tests: List[str | List[str]], prefix: str):
        return {
            f"{prefix}_{i}": (test if isinstance(test, list) else test.split("\n"))
            for i, test in enumerate(tests)
        }

    def get_tests(self, directory: Path, environ: Environment = None) -> List[str]:
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
        process = subprocess.run(
            ["python", self.access] + test,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environ,
            cwd=directory,
        )
        self.output[test_name] = (
            process.stdout.decode("utf8"),
            process.stderr.decode("utf8"),
        )
        return result
