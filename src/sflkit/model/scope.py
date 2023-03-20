from typing import List


class Var(object):
    def __init__(self, var, value, type_):
        self.var = var
        self.value = value
        self.type_ = type_

    def __hash__(self):
        return hash(self.var)

    def __eq__(self, other):
        return isinstance(other, Var) and self.var == other.var


class Scope(object):
    def __init__(self, parent=None, variables: dict = None):
        self.parent = parent
        self.variables = dict() if variables is None else variables.copy()

    def enter(self):
        return Scope(parent=self, variables=self.variables)

    def exit(self):
        if self.parent is not None:
            return self.parent
        else:
            return self

    def value(self, var: str) -> Var:
        if var in self.variables:
            return self.variables[var].value

    def add(self, var, value, type_):
        self.variables[var] = Var(var, value, type_)

    def get_all_vars(self) -> List[Var]:
        return list(self.variables.values())
