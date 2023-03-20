import ast
import unittest

from sflkit.language.python.extract import PythonVarExtract


class VarExtractionTest(unittest.TestCase):
    def _test_extract(self, expr: str, ins, outs, use=True):
        visitor = PythonVarExtract(use=use)
        tree = ast.parse(expr)
        variables = visitor.visit(tree)
        for i in ins:
            self.assertIn(i, variables)
        for o in outs:
            self.assertNotIn(o, variables)

    def test_generator(self):
        self._test_extract("[d for d in ds]", ["ds"], ["d"])
        self._test_extract("[d for d in ds if any(r for r in ds)]", ["ds"], ["d", "r"])
        self._test_extract(
            "[d + r for d in ds if any(r for r in ds)]", ["ds", "r"], ["d"]
        )
        self._test_extract(
            '[d for d in ds if d.name == "test"]', ["ds"], ["d", "d.name"]
        )
        self._test_extract("(d for d in ds)", ["ds"], ["d"])
        self._test_extract("(d for d in ds if any(r for r in ds))", ["ds"], ["d", "r"])
        self._test_extract(
            "(d + r for d in ds if any(r for r in ds))", ["ds", "r"], ["d"]
        )
        self._test_extract(
            '(d for d in ds if d.name == "test")', ["ds"], ["d", "d.name"]
        )
        self._test_extract("{d for d in ds}", ["ds"], ["d"])
        self._test_extract("{d for d in ds if any(r for r in ds)}", ["ds"], ["d", "r"])
        self._test_extract(
            "{d + r for d in ds if any(r for r in ds)}", ["ds", "r"], ["d"]
        )
        self._test_extract(
            '{d for d in ds if d.name == "test"}', ["ds"], ["d", "d.name"]
        )

    def test_lambda(self):
        self._test_extract("lambda d: d + r", ["r"], ["d"])
        self._test_extract("lambda d: d.name", [], ["d", "d.name"])

    def test_arguments(self):
        self._test_extract("def f(x=y):\n    pass", ["x"], ["y"], use=False)
        self._test_extract("f(x=y)", ["y"], ["x"])
