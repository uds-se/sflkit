import sys

sys.path = sys.path[1:] + sys.path[:1]
import enum

sys.path = sys.path[-1:] + sys.path[:-1]


class EventType(enum.Enum):
    LINE = 0
    BRANCH = 1
    FUNCTION_ENTER = 2
    FUNCTION_EXIT = 3
    FUNCTION_ERROR = 4
    DEF = 5
    USE = 6
    CONDITION = 7
    LOOP_BEGIN = 8
    LOOP_HIT = 9
    LOOP_END = 10


__all__ = ["event", "EventType"]
