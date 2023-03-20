import unittest

from sflkit.language.language import Language


class LanguageTests(unittest.TestCase):
    def test_python_equals_python3(self):
        self.assertEqual(Language.PYTHON, Language.PYTHON3)
