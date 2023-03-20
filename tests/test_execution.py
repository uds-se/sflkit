import os
import subprocess
import unittest

from sflkit import instrument_config
from sflkit.config import Config

test_resources = os.path.join("resources", "subjects", "tests")
test_dir = "test_dir"
test_events = "test_events.json"
python = "python3.10"
access = "main.py"


class EventTests(unittest.TestCase):
    def test_properties(self):
        config = Config.config(
            path=os.path.join(test_resources, "test_properties"),
            language="python",
            events="use",
            working=test_dir,
        )
        instrument_config(config)

        p = subprocess.run([python, access], cwd=test_dir)

        self.assertEqual(0, p.returncode)

    def test_undefined_use(self):
        config = Config.config(
            path=os.path.join(test_resources, "test_undefined_use"),
            language="python",
            events="use",
            working=test_dir,
        )
        instrument_config(config)

        p = subprocess.run([python, access], cwd=test_dir)

        self.assertEqual(0, p.returncode)

    def test_doc(self):
        config = Config.config(
            path=os.path.join(test_resources, "test_doc"),
            language="python",
            events="line",
            working=test_dir,
        )
        instrument_config(config)

        p = subprocess.run([python, access], cwd=test_dir)

        self.assertEqual(0, p.returncode)
