import os
import shutil
import subprocess
import unittest
from typing import List

from sflkitlib.events import event

from sflkit import instrument_config, Analyzer, Config
from sflkit.model import EventFile


class BaseTest(unittest.TestCase):
    TEST_RESOURCES = os.path.join("resources", "subjects", "tests")
    TEST_DIR = "test_dir"
    TEST_EVENTS = "test_events.json"
    TEST_PATH = "EVENTS_PATH"
    PYTHON = "python3.10"
    ACCESS = "main.py"
    TEST_LINES = "test_lines"
    TEST_BRANCHES = "test_branches"
    TEST_SUGGESTIONS = "test_suggestions"
    TEST_TYPES = "test_types"
    TEST_LOOP = "test_loop"
    TEST_PROPERTIES = "test_properties"
    TEST_SPECIAL_VALUES = "test_special_values"
    TEST_RUNNER = "test_runner"
    DELTA = 0.0000001

    EVENTS = [
        event.LineEvent("main.py", 1, 0),
        event.BranchEvent("main.py", 1, 1, 0, 1),
        event.BranchEvent("main.py", 1, 2, 1, 0),
        event.FunctionEnterEvent("main.py", 1, 3, 0, "main"),
        event.FunctionExitEvent("main.py", 1, 4, 0, "main", 1, "int", "x"),
        event.FunctionExitEvent("main.py", 1, 5, 0, "main", True, "bool", "x"),
        event.FunctionExitEvent("main.py", 1, 6, 0, "main", False, "bool", "x"),
        event.FunctionExitEvent("main.py", 1, 7, 0, "main", None, "none", "x"),
        event.FunctionExitEvent("main.py", 1, 8, 0, "main", [], "list", "x"),
        event.FunctionExitEvent("main.py", 1, 9, 0, "main", [1], "list", "x"),
        event.FunctionErrorEvent("main.py", 1, 10, 0, "main"),
        event.DefEvent("main.py", 1, 11, "x", 0, 1, "int"),
        event.DefEvent("main.py", 1, 12, "x", 0, True, "bool"),
        event.DefEvent("main.py", 1, 13, "x", 0, False, "bool"),
        event.DefEvent("main.py", 1, 14, "x", 0, None, "none"),
        event.DefEvent("main.py", 1, 15, "x", 0, [], "list"),
        event.DefEvent("main.py", 1, 16, "x", 0, [1], "list"),
        event.UseEvent("main.py", 1, 17, "x", 0),
        event.ConditionEvent("main.py", 1, 18, "x < y", True, "x"),
        event.ConditionEvent("main.py", 1, 19, "x < y", False, "x"),
        event.LoopBeginEvent("main.py", 1, 20, 0),
        event.LoopHitEvent("main.py", 1, 21, 0),
        event.LoopEndEvent("main.py", 1, 22, 0),
    ]

    @staticmethod
    def execute_subject(test: List[str], count: int):
        subprocess.run([BaseTest.PYTHON, BaseTest.ACCESS] + test, cwd=BaseTest.TEST_DIR)
        path = os.path.join(BaseTest.TEST_DIR, BaseTest.TEST_PATH + f"_{count}")
        shutil.move(os.path.join(BaseTest.TEST_DIR, BaseTest.TEST_PATH), path)
        return path

    @staticmethod
    def run_analysis(
        test: str,
        events: str,
        predicates: str,
        relevant: List[List[str]] = None,
        irrelevant: List[List[str]] = None,
    ) -> Analyzer:
        config = Config.create(
            path=os.path.join(BaseTest.TEST_RESOURCES, test),
            language="python",
            events=events,
            predicates=predicates,
            working=BaseTest.TEST_DIR,
        )
        instrument_config(config)

        relevant = list() if relevant is None else relevant
        irrelevant = list() if irrelevant is None else irrelevant

        relevant_event_files = list()
        irrelevant_event_files = list()
        count = 0

        for r in relevant:
            relevant_event_files.append(
                EventFile(BaseTest.execute_subject(r, count), count, True)
            )
            count += 1
        for r in irrelevant:
            irrelevant_event_files.append(
                EventFile(BaseTest.execute_subject(r, count), count, False)
            )
            count += 1

        analyzer = Analyzer(
            relevant_event_files, irrelevant_event_files, config.factory
        )
        analyzer.analyze()
        return analyzer
