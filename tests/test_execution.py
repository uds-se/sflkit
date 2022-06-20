import os
import subprocess
import unittest

from sflkit import instrument_config
from tests.utils import get_config

test_resources = os.path.join('..', 'resources', 'subjects', 'tests')
test_dir = 'test_dir'
test_events = 'test_events.json'
python = 'python3.9'
access = 'main.py'


class EventTests(unittest.TestCase):

    def test_properties(self):
        config = get_config(os.path.join(test_resources, 'test_properties'), 'python', 'use', None, test_dir, None,
                            None)
        instrument_config(config)

        p = subprocess.run([python, access], cwd=test_dir)

        self.assertEqual(0, p.returncode)

    def test_undefined_use(self):
        config = get_config(os.path.join(test_resources, 'test_undefined_use'), 'python', 'use', None, test_dir, None,
                            None)
        instrument_config(config)

        p = subprocess.run([python, access], cwd=test_dir)

        self.assertEqual(0, p.returncode)

    def test_doc(self):
        config = get_config(os.path.join(test_resources, 'test_doc'), 'python', 'line', None, test_dir, None,
                            None)
        instrument_config(config)

        p = subprocess.run([python, access], cwd=test_dir)

        self.assertEqual(0, p.returncode)
