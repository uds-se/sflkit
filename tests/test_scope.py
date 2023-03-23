import unittest

from sflkit.model.scope import Var, Scope


class TestScope(unittest.TestCase):
    def test_var_eq(self):
        var_1 = Var("x", 2, int)
        var_2 = Var("y", 2, int)
        var_3 = Var("x", "", str)
        self.assertEqual(var_1, var_3)
        self.assertNotEqual(var_1, var_2)
        self.assertNotEqual(var_2, var_3)
        self.assertEqual(hash(var_1), hash(var_3))
        self.assertNotEqual(hash(var_1), hash(var_2))
        self.assertNotEqual(hash(var_2), hash(var_3))

    def test_scope_without_parent(self):
        scope = Scope()
        self.assertIs(scope, scope.exit())
