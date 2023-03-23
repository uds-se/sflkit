from abc import abstractmethod, ABC


class VariableExtract(ABC):
    def setup(self, factory):
        pass

    @abstractmethod
    def visit(self, *args):
        pass


class ConditionExtract(ABC):
    def setup(self, factory):
        pass

    @abstractmethod
    def visit(self, *args):
        pass
