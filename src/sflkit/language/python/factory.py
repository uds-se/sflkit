import ast
import typing
from ast import *

from sflkit.events.event import (
    LineEvent,
    Event,
    BranchEvent,
    DefEvent,
    FunctionEnterEvent,
    FunctionErrorEvent,
    FunctionExitEvent,
    LoopBeginEvent,
    LoopHitEvent,
    LoopEndEvent,
    UseEvent,
    ConditionEvent,
)
from sflkit.language.meta import MetaVisitor, Injection, IDGenerator, TmpGenerator

python_lib = "sflkit.instrumentation.lib"


def get_call(function, *args) -> Expr:
    return Expr(
        value=Call(
            func=Attribute(
                value=Name(
                    id=python_lib,  # enter lib
                ),
                attr=function,  # enter lib function
            ),
            args=[
                Constant(
                    value=argument,
                )
                for argument in args
            ],
            keywords=[],
        ),
    )


class PythonEventFactory(MetaVisitor, NodeVisitor):
    def __init__(
        self, language, id_generator: IDGenerator, tmp_generator: TmpGenerator
    ):
        super().__init__(language, id_generator, tmp_generator)

    def visit_start(self, *args) -> Injection:
        return self.visit(*args)

    def generic_visit(self, node: AST) -> Injection:
        return Injection()

    def get_function(self):
        pass

    def get_event_call(self, event: Event):
        return get_call(self.get_function(), event.file, event.line, event.id_)


class LineEventFactory(PythonEventFactory):
    def get_function(self):
        return "add_line_event"

    def visit_line(self, node: AST) -> Injection:
        line_event = LineEvent(self.file, node.lineno, self.id_generator.get_next_id())
        return Injection(pre=[self.get_event_call(line_event)], events=[line_event])

    def visit_Assign(self, node: Assign) -> Injection:
        return self.visit_line(node)

    def visit_AnnAssign(self, node: AnnAssign) -> Injection:
        return self.visit_line(node)

    def visit_AugAssign(self, node: AugAssign) -> Injection:
        return self.visit_line(node)

    def visit_For(self, node: For) -> Injection:
        return self.visit_line(node)

    def visit_AsyncFor(self, node: AsyncFor) -> Injection:
        return self.visit_line(node)

    def visit_While(self, node: While) -> Injection:
        return self.visit_line(node)

    def visit_If(self, node: If) -> Injection:
        return self.visit_line(node)

    def visit_Try(self, node: Try) -> Injection:
        return self.visit_line(node)

    def visit_Return(self, node: Return) -> Injection:
        return self.visit_line(node)

    def visit_With(self, node: With) -> Injection:
        return self.visit_line(node)

    def visit_AsyncWith(self, node: AsyncWith) -> Injection:
        return self.visit_line(node)

    def visit_Import(self, node: Import) -> Injection:
        return self.visit_line(node)

    def visit_ImportFrom(self, node: ImportFrom) -> Injection:
        return self.visit_line(node)

    def visit_Delete(self, node: Delete) -> Injection:
        return self.visit_line(node)

    def visit_Raise(self, node: Raise) -> Injection:
        return self.visit_line(node)

    def visit_Assert(self, node: Assert) -> Injection:
        return self.visit_line(node)

    def visit_Global(self, node: Global) -> Injection:
        return self.visit_line(node)

    def visit_Nonlocal(self, node: Nonlocal) -> Injection:
        return self.visit_line(node)

    def visit_Expr(self, node: Expr) -> Injection:
        return self.visit_line(node)

    def visit_Pass(self, node: Pass) -> Injection:
        return self.visit_line(node)

    def visit_Break(self, node: Break) -> Injection:
        return self.visit_line(node)

    def visit_Continue(self, node: Continue) -> Injection:
        return self.visit_line(node)


class BranchEventFactory(PythonEventFactory):
    def __init__(
        self, language, id_generator: IDGenerator, tmp_generator: TmpGenerator
    ):
        super().__init__(language, id_generator, tmp_generator)
        self.branch_id = 0

    def get_event_call(self, event: BranchEvent):
        return get_call(
            self.get_function(),
            event.file,
            event.line,
            event.id_,
            event.then_id,
            event.else_id,
        )

    def get_function(self):
        return "add_branch_event"

    def _get_branch_events(self, node):
        then_branch_event = BranchEvent(
            self.file,
            node.lineno,
            self.id_generator.get_next_id(),
            self.branch_id,
            self.branch_id + 1,
        )
        else_branch_event = BranchEvent(
            self.file,
            node.lineno,
            self.id_generator.get_next_id(),
            self.branch_id + 1,
            self.branch_id,
        )
        self.branch_id += 2
        return then_branch_event, else_branch_event

    def _visit_branch(self, node: typing.Union[If, While, For, AsyncFor]) -> Injection:
        then_branch_event, else_branch_event = self._get_branch_events(node)
        return Injection(
            body=[self.get_event_call(then_branch_event)],
            orelse=[self.get_event_call(else_branch_event)],
            events=[then_branch_event, else_branch_event],
        )

    def visit_For(self, node: For) -> Injection:
        return self._visit_branch(node)

    def visit_AsyncFor(self, node: AsyncFor) -> Injection:
        return self._visit_branch(node)

    def visit_While(self, node: While) -> Injection:
        return self._visit_branch(node)

    def visit_If(self, node: If) -> Injection:
        return self._visit_branch(node)

    def visit_ExceptHandler(self, node: ExceptHandler) -> Injection:
        branch_event = BranchEvent(
            self.file, node.lineno, self.id_generator.get_next_id(), self.branch_id, -1
        )
        return Injection(
            body=[self.get_event_call(branch_event)], events=[branch_event]
        )

    def visit_Try(self, node: Try) -> Injection:
        else_branch_event = BranchEvent(
            self.file, node.lineno, self.id_generator.get_next_id(), self.branch_id, -1
        )
        return Injection(
            orelse=[self.get_event_call(else_branch_event)], events=[else_branch_event]
        )


class DefEventFactory(PythonEventFactory):
    def get_function(self):
        return "add_def_event"

    def get_event_call(self, event: DefEvent):
        call = get_call(
            self.get_function(), event.file, event.line, event.id_, event.var
        )
        assert isinstance(call.value, Call)
        call.value.args.append(
            Call(
                func=Attribute(
                    value=Name(
                        id=python_lib,  # enter lib
                    ),
                    attr="get_id",  # enter lib function
                ),
                args=[Name(id=event.var)],
                keywords=[],
            )
        )
        call.value.args.append(
            Name(
                id=event.var,
            )
        )
        call.value.args.append(
            Call(
                func=Attribute(
                    value=Name(
                        id=python_lib,  # enter lib
                    ),
                    attr="get_type",  # enter lib function
                ),
                args=[Name(id=event.var)],
                keywords=[],
            )
        )
        return call

    def visit_function(
        self, node: typing.Union[FunctionDef, AsyncFunctionDef]
    ) -> Injection:
        def_events = list()
        for argument in self.variable_extract.visit(node.args):
            if argument != "self":
                def_events.append(
                    DefEvent(
                        self.file,
                        node.lineno,
                        self.id_generator.get_next_id(),
                        argument,
                    )
                )
        return Injection(
            body=[self.get_event_call(e) for e in def_events], events=def_events
        )

    def visit_FunctionDef(self, node: FunctionDef) -> Injection:
        return self.visit_function(node)

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> Injection:
        return self.visit_function(node)

    def visit_var_assign(
        self, node: typing.Union[Assign, AnnAssign, AugAssign], vars_: list
    ) -> Injection:
        def_events = list()
        for var in vars_:
            def_events.append(
                DefEvent(self.file, node.lineno, self.id_generator.get_next_id(), var)
            )
        return Injection(
            post=[self.get_event_call(e) for e in def_events], events=def_events
        )

    def visit_Assign(self, node: Assign) -> Injection:
        vars_ = sum(
            [list(self.variable_extract.visit(target)) for target in node.targets],
            start=list(),
        )
        return self.visit_var_assign(node, vars_)

    def visit_AnnAssign(self, node: AnnAssign) -> Injection:
        if node.value is None:
            return Injection()
        else:
            vars_ = self.variable_extract.visit(node.target)
            return self.visit_var_assign(node, vars_)

    def visit_AugAssign(self, node: AugAssign) -> Injection:
        vars_ = self.variable_extract.visit(node.target)
        return self.visit_var_assign(node, vars_)

    def visit_for(self, node: typing.Union[For, AsyncFor]) -> Injection:
        vars_ = self.variable_extract.visit(node.target)
        def_events = list()
        for var in vars_:
            def_events.append(
                DefEvent(self.file, node.lineno, self.id_generator.get_next_id(), var)
            )
        return Injection(
            body=[self.get_event_call(e) for e in def_events], events=def_events
        )

    def visit_For(self, node: For) -> Injection:
        return self.visit_for(node)

    def visit_AsyncFor(self, node: AsyncFor) -> Injection:
        return self.visit_for(node)

    def visit_with(self, node: With | AsyncWith):
        def_events = list()
        for item in node.items:
            if item.optional_vars:
                for var in self.variable_extract.visit(item.optional_vars):
                    def_events.append(
                        DefEvent(
                            self.file, node.lineno, self.id_generator.get_next_id(), var
                        )
                    )
        if def_events:
            return Injection(
                body=[self.get_event_call(e) for e in def_events], events=def_events
            )
        return Injection()

    def visit_With(self, node: With) -> Injection:
        return self.visit_with(node)

    def visit_AsyncWith(self, node: AsyncWith) -> Injection:
        return self.visit_with(node)


class FunctionEventFactory(PythonEventFactory):
    functions: typing.Dict[AST, int] = dict()
    functions_exit_id: typing.Dict[AST, int] = dict()
    function_var: typing.Dict[AST, str] = dict()
    function_id: int = 0

    def __init__(
        self, language, id_generator: IDGenerator, tmp_generator: TmpGenerator
    ):
        super().__init__(language, id_generator, tmp_generator)
        self.function_stack = list()

    @staticmethod
    def get_function_id(node: AST) -> int:
        if node not in FunctionEventFactory.functions:
            FunctionEventFactory.functions[node] = FunctionEventFactory.function_id
            FunctionEventFactory.function_id += 1
        return FunctionEventFactory.functions[node]

    @staticmethod
    def get_function_event_id(node: AST, id_generator: IDGenerator) -> int:
        if node not in FunctionEventFactory.functions_exit_id:
            FunctionEventFactory.functions_exit_id[node] = id_generator.get_next_id()
        return FunctionEventFactory.functions_exit_id[node]

    @staticmethod
    def get_function_var(node: AST, tmp_generator: TmpGenerator) -> str:
        if node not in FunctionEventFactory.function_var:
            FunctionEventFactory.function_var[node] = tmp_generator.get_var_name()
        return FunctionEventFactory.function_var[node]

    def enter_function(self, function: AST):
        self.function_stack.append(function)

    def exit_function(self, function: AST):
        self.function_stack.pop()


class FunctionEnterEventFactory(FunctionEventFactory):
    def get_function(self):
        return "add_function_enter_event"

    def get_event_call(self, event: FunctionEnterEvent):
        return get_call(
            self.get_function(),
            event.file,
            event.line,
            event.id_,
            event.function_id,
            event.function,
        )

    def visit_function(
        self, node: typing.Union[FunctionDef, AsyncFunctionDef]
    ) -> Injection:
        function_enter_event = FunctionEnterEvent(
            self.file,
            node.lineno,
            self.id_generator.get_next_id(),
            self.get_function_id(node),
            node.name,
        )
        function_var = self.get_function_var(node, self.tmp_generator)
        return Injection(
            body=[
                self.get_event_call(function_enter_event),
                Assign(
                    targets=[
                        ast.Name(
                            id=function_var,
                        ),
                    ],
                    value=ast.Constant(value=None),
                ),
            ],
            events=[function_enter_event],
        )

    def visit_FunctionDef(self, node: FunctionDef) -> Injection:
        return self.visit_function(node)

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> Injection:
        return self.visit_function(node)


class FunctionExitEventFactor(FunctionEventFactory):
    def get_function(self):
        return "add_function_exit_event"

    def get_event_call(self, event: FunctionExitEvent):
        call = get_call(
            self.get_function(),
            event.file,
            event.line,
            event.id_,
            event.function_id,
            event.function,
        )
        assert isinstance(call.value, Call)
        call.value.args.append(Name(id=event.tmp_var))
        call.value.args.append(
            Call(
                func=Attribute(
                    value=Name(
                        id=python_lib,
                    ),
                    attr="get_type",  # enter lib function
                ),
                args=[
                    Name(
                        id=event.tmp_var,
                    )
                ],
                keywords=[],
            ),
        )
        return call

    def visit_function(
        self, node: typing.Union[FunctionDef, AsyncFunctionDef]
    ) -> Injection:
        function_exit_event = FunctionExitEvent(
            self.file,
            node.lineno,
            self.get_function_event_id(node, self.id_generator),
            self.get_function_id(node),
            node.name,
            tmp_var=self.get_function_var(node, self.tmp_generator),
        )
        return Injection(
            body_last=[self.get_event_call(function_exit_event)],
            events=[function_exit_event],
        )

    def visit_FunctionDef(self, node: FunctionDef) -> Injection:
        return self.visit_function(node)

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> Injection:
        return self.visit_function(node)

    def visit_Return(self, node: Return) -> Injection:
        function = self.function_stack[-1]
        function_var = self.get_function_var(function, self.tmp_generator)
        function_exit_event = FunctionExitEvent(
            self.file,
            node.lineno,
            self.get_function_event_id(node, self.id_generator),
            self.get_function_id(function),
            function.name,
            tmp_var=function_var,
        )
        return Injection(
            pre=[
                Assign(
                    targets=[
                        ast.Name(
                            id=function_var,
                        ),
                    ],
                    value=node.value if node.value else ast.Constant(value=None),
                ),
                self.get_event_call(function_exit_event),
            ],
            assign=ast.Name(id=function_var),
            events=[function_exit_event],
        )


class FunctionErrorEventFactory(FunctionEventFactory):
    def get_function(self):
        return "add_function_error_event"

    def get_event_call(self, event: FunctionEnterEvent | FunctionErrorEvent):
        return get_call(
            self.get_function(),
            event.file,
            event.line,
            event.id_,
            event.function_id,
            event.function,
        )

    def visit_function(
        self, node: typing.Union[FunctionDef, AsyncFunctionDef]
    ) -> Injection:
        function_error_event = FunctionErrorEvent(
            self.file,
            node.lineno,
            self.get_function_event_id(node, self.id_generator),
            self.get_function_id(node),
            node.name,
        )
        return Injection(
            error=[self.get_event_call(function_error_event)],
            events=[function_error_event],
        )

    def visit_FunctionDef(self, node: FunctionDef) -> Injection:
        return self.visit_function(node)

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> Injection:
        return self.visit_function(node)


class LoopEventFactory(PythonEventFactory):
    loops: typing.Dict[AST, int] = dict()
    loop_id: int = 0

    def get_event_call(
        self, event: typing.Union[LoopBeginEvent, LoopHitEvent, LoopEndEvent]
    ):
        return get_call(
            self.get_function(), event.file, event.line, event.id_, event.loop_id
        )

    @staticmethod
    def get_loop_id(node: AST) -> int:
        if node not in LoopEventFactory.loops:
            LoopEventFactory.loops[node] = LoopEventFactory.loop_id
            LoopEventFactory.loop_id += 1
        return LoopEventFactory.loops[node]

    def visit_loop(self, node: typing.Union[For, AsyncFor, While]) -> Injection:
        pass

    def visit_For(self, node: For) -> Injection:
        return self.visit_loop(node)

    def visit_AsyncFor(self, node: AsyncFor) -> Injection:
        return self.visit_loop(node)

    def visit_While(self, node: While) -> Injection:
        return self.visit_loop(node)


class LoopBeginEventFactory(LoopEventFactory):
    def get_function(self):
        return "add_loop_begin_event"

    def visit_loop(self, node: typing.Union[For, AsyncFor, While]) -> Injection:
        loop_begin_event = LoopBeginEvent(
            self.file,
            node.lineno,
            self.id_generator.get_next_id(),
            self.get_loop_id(node),
        )
        return Injection(
            pre=[self.get_event_call(loop_begin_event)], events=[loop_begin_event]
        )


class LoopHitEventFactory(LoopEventFactory):
    def get_function(self):
        return "add_loop_hit_event"

    def visit_loop(self, node: typing.Union[For, AsyncFor, While]) -> Injection:
        loop_hit_event = LoopHitEvent(
            self.file,
            node.lineno,
            self.id_generator.get_next_id(),
            self.get_loop_id(node),
        )
        return Injection(
            body=[self.get_event_call(loop_hit_event)], events=[loop_hit_event]
        )


class LoopEndEventFactory(LoopEventFactory):
    def get_function(self):
        return "add_loop_end_event"

    def visit_loop(self, node: typing.Union[For, AsyncFor, While]) -> Injection:
        loop_end_event = LoopEndEvent(
            self.file,
            node.lineno,
            self.id_generator.get_next_id(),
            self.get_loop_id(node),
        )
        return Injection(
            finalbody=[self.get_event_call(loop_end_event)], events=[loop_end_event]
        )


class UseEventFactory(PythonEventFactory):
    def get_function(self):
        return "add_use_event"

    def _get_try_wrapper(self, event: UseEvent):
        return Try(
            body=[self._get_wrapped_property(event)],
            handlers=[
                ExceptHandler(
                    type=Tuple(
                        elts=[
                            Name(
                                id="AttributeError",
                            ),
                            Name(
                                id="TypeError",
                            ),
                            Name(
                                id="NameError",
                            ),
                        ],
                    ),
                    name=None,
                    body=[Pass()],
                ),
            ],
            orelse=[],
            finalbody=[],
        )

    def _get_std_call(self, event: UseEvent):
        call = get_call(
            self.get_function(), event.file, event.line, event.id_, event.var
        )
        assert isinstance(call.value, Call)
        call.value.args.append(
            Call(
                func=Attribute(
                    value=Name(
                        id=python_lib,  # enter lib
                    ),
                    attr="get_id",  # enter lib function
                ),
                args=[Name(id=event.var)],
                keywords=[],
            )
        )
        return call

    def _get_wrapped_property(self, event: UseEvent):
        body = self._get_std_call(event)
        attributes = event.var.split(".")
        for i in range(len(attributes) - 1):
            class_ = ".".join(attributes[: -1 - i])
            body = If(
                test=BoolOp(
                    op=Or(),
                    values=[
                        UnaryOp(
                            op=Not(),
                            operand=Call(
                                func=Name(
                                    id="hasattr",
                                ),
                                args=[
                                    Name(id=class_ + ".__class__"),
                                    Constant(
                                        value=attributes[-1 - i],
                                    ),
                                ],
                                keywords=[],
                            ),
                        ),
                        UnaryOp(
                            op=Not(),
                            operand=Call(
                                func=Name(
                                    id="isinstance",
                                ),
                                args=[
                                    Name(
                                        id=class_ + ".__class__." + attributes[-1 - i]
                                    ),
                                    Name(
                                        id="property",
                                    ),
                                ],
                                keywords=[],
                            ),
                        ),
                    ],
                ),
                body=[body],
                orelse=[],
            )
        return body

    def get_event_call(self, event: UseEvent):
        return self._get_try_wrapper(event)

    def visit_use(self, node: AST):
        uses = self.use_extract.visit(node)
        use_events = list()
        for use in uses:
            use_events.append(
                UseEvent(self.file, node.lineno, self.id_generator.get_next_id(), use)
            )
        return Injection(
            pre=[self.get_event_call(e) for e in use_events], events=use_events
        )

    def visit_Assign(self, node: Assign) -> Injection:
        return self.visit_use(node.value)

    def visit_AnnAssign(self, node: AnnAssign) -> Injection:
        if node.value is None:
            return Injection()
        else:
            return self.visit_use(node.value)

    def visit_AugAssign(self, node: AugAssign) -> Injection:
        return self.visit_use(node.target) + self.visit_use(node.value)

    def visit_loop(self, node: AST):
        injection = self.visit_use(node)
        if isinstance(node, While):
            injection.body_last = injection.pre
        return injection

    def visit_For(self, node: For) -> Injection:
        return self.visit_loop(node.iter)

    def visit_AsyncFor(self, node: AsyncFor) -> Injection:
        return self.visit_loop(node.iter)

    def visit_While(self, node: While) -> Injection:
        return self.visit_loop(node.test)

    def visit_If(self, node: If) -> Injection:
        return self.visit_use(node.test)

    def visit_Return(self, node: Return) -> Injection:
        return self.visit_use(node.value)

    def visit_With(self, node: With) -> Injection:
        return sum(
            [self.visit_use(item.context_expr) for item in node.items],
            start=Injection(),
        )

    def visit_AsyncWith(self, node: AsyncWith) -> Injection:
        return sum(
            [self.visit_use(item.context_expr) for item in node.items],
            start=Injection(),
        )

    def visit_Delete(self, node: Delete) -> Injection:
        return sum(
            [self.visit_use(target) for target in node.targets], start=Injection()
        )

    def visit_Raise(self, node: Raise) -> Injection:
        return self.visit_use(node.exc)

    def visit_Assert(self, node: Assert) -> Injection:
        return self.visit_use(node.test)

    def visit_Expr(self, node: Expr) -> Injection:
        return self.visit_use(node.value)

    def visit_Global(self, node: Global) -> Injection:
        return self.visit_use(node)

    def visit_Nonlocal(self, node: Nonlocal) -> Injection:
        return self.visit_use(node)


class ConditionEventFactory(PythonEventFactory):
    def get_function(self):
        return "add_condition_event"

    def get_event_call(self, event: ConditionEvent):
        call = get_call(
            self.get_function(),
            event.file,
            event.line,
            event.id_,
            event.condition,
        )
        assert isinstance(call.value, Call)
        call.value.args.append(
            Name(
                id=event.tmp_var,
            )
        )
        return call

    def visit_condition(self, node: typing.Union[If, While]) -> Injection:
        self.condition_extract.setup(self)
        var, var_use, var_assign, events = self.condition_extract.visit(node.test)
        return Injection(pre=[var_assign], assign=var_use, events=events)

    def visit_While(self, node: While) -> Injection:
        return self.visit_condition(node)

    def visit_If(self, node: If) -> Injection:
        return self.visit_condition(node)
