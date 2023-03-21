from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.predicate import (
    Branch,
    Condition,
    ScalarPair,
    Comp,
    VariablePredicate,
    ReturnPredicate,
    NonePredicate,
    EmptyStringPredicate,
    EmptyBytesPredicate,
    IsAsciiPredicate,
    ContainsDigitPredicate,
    ContainsSpecialPredicate,
)
from sflkit.analysis.spectra import Line, Function, Loop, DefUse
from sflkit.events import EventType
from sflkit.events.event import (
    LineEvent,
    BranchEvent,
    FunctionEnterEvent,
    LoopBeginEvent,
    DefEvent,
    UseEvent,
    FunctionExitEvent,
)
from utils import BaseTest


class TestAnalysisObjects(BaseTest):
    def test_line(self):
        obj = Line(LineEvent(self.ACCESS, 1, 0))
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual(AnalysisType.LINE, obj.analysis_type())
        self.assertEqual(1, len(obj.events()))
        self.assertIn(EventType.LINE, obj.events())

    def test_branch(self):
        obj = Branch(BranchEvent(self.ACCESS, 1, 0, 0, 1), then=False)
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual(1, obj.then_id)
        self.assertFalse(obj.then)
        self.assertEqual(AnalysisType.BRANCH, obj.analysis_type())
        self.assertEqual(1, len(obj.events()))
        self.assertIn(EventType.BRANCH, obj.events())

    def test_function(self):
        obj = Function(FunctionEnterEvent(self.ACCESS, 1, 0, 0, "main"))
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual("main", obj.function)
        self.assertEqual(AnalysisType.FUNCTION, obj.analysis_type())
        self.assertEqual(1, len(obj.events()))
        self.assertIn(EventType.FUNCTION_ENTER, obj.events())

    def test_loop(self):
        obj = Loop(LoopBeginEvent(self.ACCESS, 1, 0, 0))
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual(AnalysisType.LOOP, obj.analysis_type())
        self.assertEqual(3, len(obj.events()))
        self.assertIn(EventType.LOOP_BEGIN, obj.events())
        self.assertIn(EventType.LOOP_HIT, obj.events())
        self.assertIn(EventType.LOOP_END, obj.events())

    def test_def_use(self):
        obj = DefUse(
            DefEvent(self.ACCESS, 1, 0, "x", 0), UseEvent(self.ACCESS, 2, 0, "x", 0)
        )
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual(self.ACCESS, obj.use_file)
        self.assertEqual(2, obj.use_line)
        self.assertEqual("x", obj.var)
        self.assertEqual(AnalysisType.DEF_USE, obj.analysis_type())
        self.assertEqual(2, len(obj.events()))
        self.assertIn(EventType.DEF, obj.events())
        self.assertIn(EventType.USE, obj.events())

    def test_condition(self):
        obj = Condition(self.ACCESS, 1, "x < y")
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual("x < y", obj.condition)
        self.assertEqual(AnalysisType.CONDITION, obj.analysis_type())
        self.assertEqual(1, len(obj.events()))
        self.assertIn(EventType.CONDITION, obj.events())

    def test_scalar_pair(self):
        obj = ScalarPair(DefEvent(self.ACCESS, 1, 0, "x", 0), Comp.LT, "y")
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual(Comp.LT, obj.op)
        self.assertEqual("x", obj.var1)
        self.assertEqual("y", obj.var2)
        self.assertEqual(AnalysisType.SCALAR_PAIR, obj.analysis_type())
        self.assertEqual(4, len(obj.events()))
        self.assertIn(EventType.DEF, obj.events())
        self.assertIn(EventType.FUNCTION_ENTER, obj.events())
        self.assertIn(EventType.FUNCTION_EXIT, obj.events())
        self.assertIn(EventType.FUNCTION_ERROR, obj.events())

    def test_variable(self):
        obj = VariablePredicate(DefEvent(self.ACCESS, 1, 0, "x", 0), Comp.LT)
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual(Comp.LT, obj.op)
        self.assertEqual("x", obj.var)
        self.assertEqual(AnalysisType.VARIABLE, obj.analysis_type())
        self.assertEqual(1, len(obj.events()))
        self.assertIn(EventType.DEF, obj.events())

    def test_return(self):
        obj = ReturnPredicate(
            FunctionExitEvent(self.ACCESS, 1, 0, 0, "main", 1), Comp.LT, 2
        )
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual(Comp.LT, obj.op)
        self.assertEqual(2, obj.value)
        self.assertEqual(AnalysisType.RETURN, obj.analysis_type())
        self.assertEqual(3, len(obj.events()))
        self.assertIn(EventType.FUNCTION_ENTER, obj.events())
        self.assertIn(EventType.FUNCTION_EXIT, obj.events())
        self.assertIn(EventType.FUNCTION_ERROR, obj.events())

    def test_none(self):
        obj = NonePredicate(DefEvent(self.ACCESS, 1, 0, "x", 0))
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual(obj.op, Comp.EQ)
        self.assertEqual("x", obj.var)
        self.assertEqual(AnalysisType.NONE, obj.analysis_type())
        self.assertIsNone(getattr(obj, "_get_second")(None))
        self.assertEqual(1, len(obj.events()))
        self.assertIn(EventType.DEF, obj.events())

    def test_empty_string(self):
        obj = EmptyStringPredicate(DefEvent(self.ACCESS, 1, 0, "x", 0))
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual(obj.op, Comp.EQ)
        self.assertEqual("x", obj.var)
        self.assertEqual(AnalysisType.EMPTY_STRING, obj.analysis_type())
        self.assertEqual("", getattr(obj, "_get_second")(None))
        self.assertEqual(1, len(obj.events()))
        self.assertIn(EventType.DEF, obj.events())

    def test_ascii_string(self):
        obj = IsAsciiPredicate(DefEvent(self.ACCESS, 1, 0, "x", 0))
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual("x", obj.var)
        self.assertEqual(AnalysisType.ASCII_STRING, obj.analysis_type())
        self.assertTrue(obj.predicate("test1"))
        self.assertFalse(obj.predicate("test§"))
        self.assertEqual(1, len(obj.events()))
        self.assertIn(EventType.DEF, obj.events())

    def test_digit_string(self):
        obj = ContainsDigitPredicate(DefEvent(self.ACCESS, 1, 0, "x", 0))
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual("x", obj.var)
        self.assertEqual(AnalysisType.DIGIT_STRING, obj.analysis_type())
        self.assertTrue(obj.predicate("test1"))
        self.assertFalse(obj.predicate("test"))
        self.assertEqual(1, len(obj.events()))
        self.assertIn(EventType.DEF, obj.events())

    def test_special_string(self):
        obj = ContainsSpecialPredicate(DefEvent(self.ACCESS, 1, 0, "x", 0))
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual("x", obj.var)
        self.assertEqual(AnalysisType.SPECIAL_STRING, obj.analysis_type())
        self.assertTrue(obj.predicate("test."))
        self.assertFalse(obj.predicate("test1"))
        self.assertEqual(1, len(obj.events()))
        self.assertIn(EventType.DEF, obj.events())

    def test_empty_bytes(self):
        obj = EmptyBytesPredicate(DefEvent(self.ACCESS, 1, 0, "x", 0))
        self.assertEqual(self.ACCESS, obj.file)
        self.assertEqual(1, obj.line)
        self.assertEqual(obj.op, Comp.EQ)
        self.assertEqual("x", obj.var)
        self.assertEqual(AnalysisType.EMPTY_BYTES, obj.analysis_type())
        self.assertEqual(b"", getattr(obj, "_get_second")(None))
        self.assertEqual(1, len(obj.events()))
        self.assertIn(EventType.DEF, obj.events())
