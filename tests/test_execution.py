import os
import subprocess

from sflkit import instrument_config
from sflkit.config import Config
from utils import BaseTest


class EventTests(BaseTest):
    def test_properties(self):
        config = Config.create(
            path=os.path.join(self.TEST_RESOURCES, self.TEST_PROPERTIES),
            language="python",
            events="use",
            working=self.TEST_DIR,
        )
        instrument_config(config)

        p = subprocess.run([self.PYTHON, self.ACCESS], cwd=self.TEST_DIR)

        self.assertEqual(0, p.returncode)

    def test_undefined_use(self):
        config = Config.create(
            path=os.path.join(self.TEST_RESOURCES, "test_undefined_use"),
            language="python",
            events="use",
            working=self.TEST_DIR,
        )
        instrument_config(config)

        p = subprocess.run([self.PYTHON, self.ACCESS], cwd=self.TEST_DIR)

        self.assertEqual(0, p.returncode)

    def test_doc(self):
        config = Config.create(
            path=os.path.join(self.TEST_RESOURCES, "test_doc"),
            language="python",
            events="line",
            working=self.TEST_DIR,
        )
        instrument_config(config)

        p = subprocess.run([self.PYTHON, self.ACCESS], cwd=self.TEST_DIR)

        self.assertEqual(0, p.returncode)
