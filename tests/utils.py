import os
import shutil
import subprocess
import unittest
from typing import List

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
    TEST_PROPERTIES = "test_properties"

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
        config = Config.config(
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
