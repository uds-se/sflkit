from abc import abstractmethod


class VariableExtract:
    @abstractmethod
    def setup(self, factory):
        pass

    @abstractmethod
    def visit(self, *args):
        pass


class ConditionExtract:
    @abstractmethod
    def setup(self, factory):
        pass

    @abstractmethod
    def visit(self, *args):
        pass
