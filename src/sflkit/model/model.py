from typing import List

from sflkit.model.scope import Scope


class Model(object):
    def __init__(self, factory):
        self.factory = factory
        self.variables = Scope()
        self.returns = Scope()
        self.current_run_id = None

    def prepare(self, run_id):
        self.factory.reset()
        self.variables = Scope()
        self.returns = Scope()
        self.current_run_id = run_id

    def handle_event(self, event, scope: Scope = None):
        analysis = self.factory.handle(event, scope=scope)
        for a in analysis:
            a.hit(self.current_run_id, event, scope)

    def handle_line_event(self, event):
        self.handle_event(event)

    def handle_branch_event(self, event):
        self.handle_event(event)

    def handle_function_enter_event(self, event):
        self.enter_scope()
        self.handle_event(event)

    def handle_function_exit_event(self, event):
        self.returns.add(event.function, event.return_value, event.type_)
        self.handle_event(event, self.returns)
        self.exit_scope()

    def handle_function_error_event(self, event):
        self.handle_event(event)
        self.exit_scope()

    def handle_def_event(self, event):
        self.variables.add(event.var, event.value, event.type_)
        self.handle_event(event, self.variables)

    def handle_use_event(self, event):
        self.handle_event(event, self.variables)

    def handle_condition_event(self, event):
        self.handle_event(event)

    def handle_loop_begin_event(self, event):
        self.handle_event(event)

    def handle_loop_hit_event(self, event):
        self.handle_event(event)

    def handle_loop_end_event(self, event):
        self.handle_event(event)

    def enter_scope(self):
        self.variables = self.variables.enter()

    def exit_scope(self):
        self.variables = self.variables.exit()

    def get_analysis(self) -> List:
        return self.factory.get_all()

    def finalize(self, passed, failed):
        for p in self.get_analysis():
            p.analyze(passed, failed)
