import unittest
from middle import middle


class MiddleTests(unittest.TestCase):
    def test_213(self):
        self.assertEqual(middle(2, 1, 3), 2)

    def test_321(self):
        self.assertEqual(middle(3, 2, 1), 2)

    def test_312(self):
        self.assertEqual(middle(3, 1, 2), 2)
