import unittest

from sflkit.language.language import Language


class LanguageTests(unittest.TestCase):

    def test_python_equals_python3(self):
        self.assertEqual(type(Language.PYTHON.visitor), type(Language.PYTHON3.visitor))
        self.assertEqual(type(Language.PYTHON.suffixes), type(Language.PYTHON3.suffixes))
