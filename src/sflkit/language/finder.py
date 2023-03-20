class LocationsFinder:
    def __init__(self, file: str, line: int):
        self.file = file
        self.line = line
        self.lines = {line}

    def get_locations(self, base_dir: str):
        pass


class FunctionFinder(LocationsFinder):
    def __init__(self, file: str, line: int, target: str):
        super().__init__(file, line)
        self.target = target


class LoopFinder(LocationsFinder):
    pass


class BranchFinder(LocationsFinder):
    def __init__(self, file: str, line: int, then: bool):
        super().__init__(file, line)
        self.then = then
