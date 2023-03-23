import enum
from typing import List, Dict, Type

import sflkit.language.python.factory as python_factory
from sflkit.analysis.analysis_type import AnalysisObject
from sflkit.events import EventType
from sflkit.language.extract import VariableExtract, ConditionExtract
from sflkit.language.finder import BranchFinder, LoopFinder, FunctionFinder
from sflkit.language.meta import MetaVisitor
from sflkit.language.python.extract import PythonVarExtract, PythonConditionExtract
from sflkit.language.python.finder import (
    PythonFunctionFinder,
    PythonLoopFinder,
    PythonBranchFinder,
)
from sflkit.language.python.visitor import PythonInstrumentation
from sflkit.language.visitor import ASTVisitor


class Language(enum.Enum):
    def __init__(
        self,
        ast_visitor: Type[ASTVisitor],
        meta_visitors: Dict[EventType, Type[MetaVisitor]],
        var_extract: VariableExtract,
        use_extract: VariableExtract,
        condition_extract: ConditionExtract,
        function_finder: FunctionFinder,
        loop_finder: LoopFinder,
        branch_finder: BranchFinder,
        suffixes: List[str],
    ):
        self.visitor = ast_visitor
        self.meta_visitors = meta_visitors
        self.var_extract = var_extract
        self.use_extract = use_extract
        self.condition_extract = condition_extract
        self.function_finder = function_finder
        self.loop_finder = loop_finder
        self.branch_finder = branch_finder
        self.suffixes = suffixes

    def setup(self):
        AnalysisObject.set_finder(
            self.function_finder, self.loop_finder, self.branch_finder
        )

    PYTHON = (
        PythonInstrumentation,
        {
            EventType.LINE: python_factory.LineEventFactory,
            EventType.BRANCH: python_factory.BranchEventFactory,
            EventType.DEF: python_factory.DefEventFactory,
            EventType.USE: python_factory.UseEventFactory,
            EventType.LOOP_BEGIN: python_factory.LoopBeginEventFactory,
            EventType.LOOP_HIT: python_factory.LoopHitEventFactory,
            EventType.LOOP_END: python_factory.LoopEndEventFactory,
            EventType.FUNCTION_ENTER: python_factory.FunctionEnterEventFactory,
            EventType.FUNCTION_EXIT: python_factory.FunctionExitEventFactor,
            EventType.FUNCTION_ERROR: python_factory.FunctionErrorEventFactory,
            EventType.CONDITION: python_factory.ConditionEventFactory,
        },
        PythonVarExtract(),
        PythonVarExtract(use=True),
        PythonConditionExtract(),
        PythonFunctionFinder,
        PythonLoopFinder,
        PythonBranchFinder,
        ["py"],
    )  # Equals PYTHON3
    PYTHON3 = PYTHON
    PYTHON2 = (
        None,
        {
            EventType.LINE: python_factory.LineEventFactory,
            EventType.BRANCH: python_factory.BranchEventFactory,
            EventType.DEF: python_factory.DefEventFactory,
            EventType.USE: python_factory.UseEventFactory,
            EventType.LOOP_BEGIN: python_factory.LoopBeginEventFactory,
            EventType.LOOP_HIT: python_factory.LoopHitEventFactory,
            EventType.LOOP_END: python_factory.LoopEndEventFactory,
            EventType.FUNCTION_ENTER: python_factory.FunctionEnterEventFactory,
            EventType.FUNCTION_EXIT: python_factory.FunctionExitEventFactor,
            EventType.FUNCTION_ERROR: python_factory.FunctionEnterEventFactory,
            EventType.CONDITION: python_factory.ConditionEventFactory,
        },
        PythonVarExtract(),
        PythonVarExtract(use=True),
        PythonConditionExtract(),
        PythonFunctionFinder,
        PythonLoopFinder,
        PythonBranchFinder,
        ["py"],
    )
    C = (None, dict(), None, None, None, None, None, None, ["c", "h"])
