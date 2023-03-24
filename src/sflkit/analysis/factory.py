from abc import abstractmethod
from typing import List, Type, Set

from sflkit.analysis.analysis_type import AnalysisObject, AnalysisType
from sflkit.analysis.predicate import (
    Branch,
    Condition,
    Comp,
    ScalarPair,
    VariablePredicate,
    ReturnPredicate,
    NonePredicate,
    EmptyStringPredicate,
    IsAsciiPredicate,
    ContainsDigitPredicate,
    ContainsSpecialPredicate,
    EmptyBytesPredicate,
)
from sflkit.analysis.spectra import Line, Function, Loop, DefUse
from sflkit.events import EventType
from sflkit.model.scope import Scope


class AnalysisFactory:
    def __init__(self):
        self.objects = dict()

    @abstractmethod
    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        raise NotImplementedError()

    def handle(self, event, scope: Scope = None):
        analysis = self.get_analysis(event, scope=scope)
        if analysis:
            return analysis
        else:
            return self.default()

    def reset(self):
        pass

    @staticmethod
    def default():
        return list()

    def get_all(self) -> Set[AnalysisObject]:
        return set(self.objects.values())


class CombinationFactory(AnalysisFactory):
    def __init__(self, factories: List[AnalysisFactory]):
        super().__init__()
        self.factories = factories

    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        return sum(
            [factory.handle(event, scope) for factory in self.factories], start=list()
        )

    def reset(self):
        [f.reset() for f in self.factories]

    def get_all(self) -> Set[AnalysisObject]:
        return set().union(*map(lambda f: f.get_all(), self.factories))


class LineFactory(AnalysisFactory):
    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        if event.event_type == EventType.LINE:
            key = (Line.analysis_type(), event.file, event.line)
            if key not in self.objects:
                self.objects[key] = Line(event)
            return [self.objects[key]]


class BranchFactory(AnalysisFactory):
    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        if event.event_type == EventType.BRANCH:
            key = (Branch.analysis_type(), event.file, event.line, event.then_id)
            then = event.then_id < event.else_id
            if key not in self.objects:
                self.objects[key] = Branch(event, then=then)
            if event.else_id >= 0:
                else_key = (
                    Branch.analysis_type(),
                    event.file,
                    event.line,
                    event.else_id,
                )
                if else_key not in self.objects:
                    self.objects[else_key] = Branch(event, then=not then)
                return [self.objects[key], self.objects[else_key]]
            return [self.objects[key]]


class FunctionFactory(AnalysisFactory):
    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        if event.event_type == EventType.FUNCTION_ENTER:
            key = (Function.analysis_type(), event.file, event.line, event.function_id)
            if key not in self.objects:
                self.objects[key] = Function(event)
            return [self.objects[key]]


class LoopFactory(AnalysisFactory):
    def get_all(self) -> Set[AnalysisObject]:
        return set(obj for value in self.objects.values() for obj in value)

    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        if event.event_type in (
            EventType.LOOP_BEGIN,
            EventType.LOOP_HIT,
            EventType.LOOP_END,
        ):
            key = (Loop.analysis_type(), event.file, event.line, event.loop_id)
            if key not in self.objects:
                self.objects[key] = [
                    Loop(event, Loop.evaluate_hit_0),
                    Loop(event, Loop.evaluate_hit_1),
                    Loop(event, Loop.evaluate_hit_more),
                ]
            if event.event_type == EventType.LOOP_BEGIN:
                list(map(Loop.start_loop, self.objects[key]))
            elif event.event_type == EventType.LOOP_HIT:
                list(map(Loop.hit_loop, self.objects[key]))
            elif event.event_type == EventType.LOOP_END:
                return self.objects[key][:]
            return list()


class DefUseFactory(AnalysisFactory):
    def __init__(self):
        super().__init__()
        self.id_to_def = dict()

    def reset(self):
        self.id_to_def = dict()

    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        if event.event_type == EventType.DEF:
            self.id_to_def[event.var_id] = event
        elif event.event_type == EventType.USE:
            if event.var_id in self.id_to_def:
                key = (
                    DefUse.analysis_type(),
                    self.id_to_def[event.var_id].file,
                    self.id_to_def[event.var_id].line,
                    event.file,
                    event.line,
                    event.var,
                )
                if key not in self.objects:
                    self.objects[key] = DefUse(self.id_to_def[event.var_id], event)
                return [self.objects[key]]


class ConditionFactory(AnalysisFactory):
    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        if event.event_type == EventType.CONDITION:

            key = (Condition.analysis_type(), event.file, event.line, event.condition)
            if key not in self.objects:
                self.objects[key] = Condition(event.file, event.line, event.condition)
            return [self.objects[key]]


class ScalarPairFactory(AnalysisFactory):
    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        if event.event_type == EventType.DEF:
            variables = scope.get_all_vars()
            objects = list()
            if event.type_ in ["int", "float", "bool", "str", "bytes"]:
                for types in (["int", "float", "bool"], ["str"], ["bytes"]):
                    if event.type_ in types:
                        for variable in variables:
                            if variable.var != event.var:
                                if variable.type_ in types:
                                    for comp in Comp:
                                        key = (
                                            ScalarPair.analysis_type(),
                                            event.file,
                                            event.line,
                                            event.var,
                                            variable.var,
                                            comp,
                                            types[0],
                                        )
                                        if key not in self.objects:
                                            self.objects[key] = ScalarPair(
                                                event, comp, variable.var
                                            )
                                        objects.append(self.objects[key])
            else:
                for variable in variables:
                    if variable.type_ == event.type_:
                        for comp in (Comp.EQ, Comp.NE):
                            key = (
                                ScalarPair.analysis_type(),
                                event.file,
                                event.line,
                                event.var,
                                variable.var,
                                comp,
                                event.type_,
                            )
                            if key not in self.objects:
                                self.objects[key] = ScalarPair(
                                    event, comp, variable.var
                                )
                            objects.append(self.objects[key])
            return objects


class VariableFactory(AnalysisFactory):
    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        if event.event_type == EventType.DEF and event.type_ in [
            "int",
            "float",
            "bool",
        ]:
            objects = list()
            for comp in Comp:
                key = (
                    VariablePredicate.analysis_type(),
                    event.file,
                    event.line,
                    event.var,
                    comp,
                    "int",
                )
                if key not in self.objects:
                    self.objects[key] = VariablePredicate(event, comp)
                objects.append(self.objects[key])
            return objects


class ReturnFactory(AnalysisFactory):
    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        if event.event_type == EventType.FUNCTION_EXIT:
            objects = list()
            if event.type_ in ("int", "float", "bool", "str", "bytes"):
                if event.type_ in ("int", "float", "bool"):
                    type_, tr = "num", 0
                    compare = Comp
                elif event.type_ == "str":
                    type_, tr = "str", ""
                    compare = Comp.EQ, Comp.NE
                else:
                    type_, tr = "bytes", b""
                    compare = Comp.EQ, Comp.NE
                for comp in compare:
                    key = (
                        ReturnPredicate.analysis_type(),
                        event.file,
                        event.line,
                        event.function,
                        comp,
                        type_,
                    )
                    if key not in self.objects:
                        self.objects[key] = ReturnPredicate(event, comp, value=tr)
                    objects.append(self.objects[key])
            if event.type_ == "NoneType":
                for comp in Comp.EQ, Comp.NE:
                    key = (
                        ReturnPredicate.analysis_type(),
                        event.file,
                        event.line,
                        event.function,
                        comp,
                        event.type_,
                    )
                    if key not in self.objects:
                        self.objects[key] = ReturnPredicate(event, comp, value=None)
                    objects.append(self.objects[key])
            else:
                for comp in Comp.EQ, Comp.NE:
                    key = (
                        ReturnPredicate.analysis_type(),
                        event.file,
                        event.line,
                        event.function,
                        comp,
                        "NoneType",
                    )
                    if key in self.objects:
                        objects.append(self.objects[key])
            return objects


class ConstantCompFactory(AnalysisFactory):
    def __init__(self, class_: Type[AnalysisObject]):
        super().__init__()
        self.class_ = class_

    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        if event.event_type == EventType.DEF:
            objects = list()
            for comp in Comp.EQ, Comp.NE:
                key = (
                    self.class_.analysis_type(),
                    event.file,
                    event.line,
                    event.var,
                    comp,
                )
                if key not in self.objects:
                    self.objects[key] = self.class_(event)
                objects.append(self.objects[key])
            return objects


class NoneFactory(ConstantCompFactory):
    def __init__(self):
        super().__init__(NonePredicate)


class EmptyStringFactory(ConstantCompFactory):
    def __init__(self):
        super().__init__(EmptyStringPredicate)


class EmptyBytesFactory(ConstantCompFactory):
    def __init__(self):
        super().__init__(EmptyBytesPredicate)


class PredicateFunctionFactory(AnalysisFactory):
    def __init__(self, class_: Type[AnalysisObject]):
        super().__init__()
        self.class_ = class_

    def get_analysis(self, event, scope: Scope = None) -> List[AnalysisObject]:
        if event.event_type == EventType.DEF:
            key = (
                self.class_.analysis_type(),
                event.file,
                event.line,
                event.var,
            )
            if key not in self.objects:
                self.objects[key] = self.class_(event)
            return [self.objects[key]]


class IsAsciiFactory(PredicateFunctionFactory):
    def __init__(self):
        super().__init__(IsAsciiPredicate)


class ContainsDigitFactory(PredicateFunctionFactory):
    def __init__(self):
        super().__init__(ContainsDigitPredicate)


class ContainsSpecialFactory(PredicateFunctionFactory):
    def __init__(self):
        super().__init__(ContainsSpecialPredicate)


analysis_factory_mapping = {
    AnalysisType.LINE: LineFactory,
    AnalysisType.BRANCH: BranchFactory,
    AnalysisType.LOOP: LoopFactory,
    AnalysisType.CONDITION: ConditionFactory,
    AnalysisType.NONE: NoneFactory,
    AnalysisType.DEF_USE: DefUseFactory,
    AnalysisType.SPECIAL_STRING: ContainsSpecialFactory,
    AnalysisType.DIGIT_STRING: ContainsDigitFactory,
    AnalysisType.ASCII_STRING: IsAsciiFactory,
    AnalysisType.EMPTY_BYTES: EmptyBytesFactory,
    AnalysisType.EMPTY_STRING: EmptyStringFactory,
    AnalysisType.RETURN: ReturnFactory,
    AnalysisType.VARIABLE: VariableFactory,
    AnalysisType.SCALAR_PAIR: ScalarPairFactory,
    AnalysisType.FUNCTION: FunctionFactory,
}
