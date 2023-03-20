import enum

from sflkit.runners.run import Runner, VoidRunner


class RunnerType(enum.Enum):
    def __init__(self, runner: Runner):
        self.runner = runner

    VOID_RUNNER = VoidRunner
