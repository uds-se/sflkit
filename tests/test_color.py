import unittest

from sflkit.analysis.suggestion import Suggestion, Location
from sflkit.color import ColorCode


class TestColor(unittest.TestCase):
    def test_color(self):
        color = ColorCode(
            [
                Suggestion([Location("main.py", 1)], 1),
                Suggestion([Location("main.py", 2)], 0.4),
                Suggestion([Location("main.py", 3)], 0.8),
            ]
        )
        html = color.code(
            "main.py",
            "x = 1\ny = 2\nz = 3",
            color=True,
            suspiciousness=True,
            line_numbers=True,
        )
        self.assertIn('title="Line 1: 100%"', html)
        self.assertIn('title="Line 2:  40%"', html)
        self.assertIn('title="Line 3:  80%"', html)
        self.assertIn('style="background-color:#ff9999"', html)
        self.assertIn('style="background-color:#f0fa9e"', html)
        self.assertIn('style="background-color:#ffc299"', html)
        self.assertIn("1 100% x = 1", html)
        self.assertIn("2  40% y = 2", html)
        self.assertIn("3  80% z = 3", html)
