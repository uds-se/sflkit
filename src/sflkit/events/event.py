import sys
from abc import abstractmethod
from typing import Any, List

from sflkit.events import EventType
from sflkit.model.model import Model

sys.path = sys.path[1:] + sys.path[:1]
import csv
import json
import pickle
import base64

sys.path = sys.path[-1:] + sys.path[:-1]


class Event(object):
    def __init__(self, file: str, line: int, id_: int, event_type: EventType):
        self.file = file
        self.line = line
        self.id_ = id_
        self.event_type = event_type

    def __hash__(self):
        return hash((self.file, self.line, self.id_, self.event_type.value))

    def __eq__(self, other):
        if isinstance(other, Event):
            return (
                self.file == other.file
                and self.line == other.line
                and self.id_ == other.id_
                and self.event_type == other.event_type
            )
        return False

    def __repr__(self):
        return f"{self.__class__.__name__}({self.file},{self.line},{self.id_})"

    @abstractmethod
    def handle(self, model: Model):
        raise NotImplementedError()

    def serialize(self):
        return {
            "file": self.file,
            "line": self.line,
            "id": self.id_,
            "event_type": self.event_type.value,
        }

    def dump(self) -> list:
        return [self.event_type.value, self.file, self.line, self.id_]

    @staticmethod
    def deserialize(s: dict):
        return None


class EventEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Event):
            return o.serialize()
        else:
            super().default(o)


class LineEvent(Event):
    def __init__(self, file: str, line: int, id_: int):
        super().__init__(file, line, id_, EventType.LINE)

    def handle(self, model: Model):
        model.handle_line_event(self)

    @staticmethod
    def deserialize(s: dict):
        assert all(p in s for p in ["file", "line", "id"])
        assert s["event_type"] == EventType.LINE.value
        return LineEvent(*[s[p] for p in ["file", "line", "id"]])


class BranchEvent(Event):
    def __init__(self, file: str, line: int, id_: int, then_id: int, else_id: int):
        super().__init__(file, line, id_, EventType.BRANCH)
        self.then_id = then_id
        self.else_id = else_id

    def handle(self, model: Model):
        model.handle_branch_event(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.file},{self.line},{self.id_},{self.then_id},{self.else_id})"

    def serialize(self):
        default = super().serialize()
        default["then_id"] = self.then_id
        default["else_id"] = self.else_id
        return default

    def dump(self):
        return super().dump() + [self.then_id] + [self.else_id]

    @staticmethod
    def deserialize(s: dict):
        assert all(p in s for p in ["file", "line", "id", "then_id", "else_id"])
        assert s["event_type"] == EventType.BRANCH.value
        return BranchEvent(
            *[s[p] for p in ["file", "line", "id", "then_id", "else_id"]]
        )


class DefEvent(Event):
    def __init__(
        self,
        file,
        line: int,
        id_: int,
        var: str,
        var_id: int = None,
        value: Any = None,
        type_: str = None,
    ):
        super().__init__(file, line, id_, EventType.DEF)
        self.var = var
        self.var_id = var_id
        self.value = value
        self.type_ = type_

    def __repr__(self):
        return f"{self.__class__.__name__}({self.file},{self.line},{self.id_},{self.var},{self.var_id},{self.value})"

    def handle(self, model: Model):
        model.handle_def_event(self)

    def serialize(self):
        default = super().serialize()
        default["var"] = self.var
        return default

    def dump(self):
        return super().dump() + [self.var, self.var_id, self.value, self.type_]

    @staticmethod
    def deserialize(s: dict):
        assert all(p in s for p in ["file", "line", "id", "var"])
        assert s["event_type"] == EventType.DEF.value
        return DefEvent(*[s[p] for p in ["file", "line", "id", "var"]])


class FunctionEnterEvent(Event):
    def __init__(self, file: str, line: int, id_: int, function_id: int, function: str):
        super().__init__(file, line, id_, EventType.FUNCTION_ENTER)
        self.function_id = function_id
        self.function = function

    def __repr__(self):
        return f"{self.__class__.__name__}({self.file},{self.line},{self.id_},{self.function})"

    def handle(self, model: Model):
        model.handle_function_enter_event(self)

    def serialize(self):
        default = super().serialize()
        default["function_id"] = self.function_id
        default["function"] = self.function
        return default

    def dump(self):
        return super().dump() + [self.function_id, self.function]

    @staticmethod
    def deserialize(s: dict):
        assert all(p in s for p in ["file", "line", "id", "function_id", "function"])
        assert s["event_type"] == EventType.FUNCTION_ENTER.value
        return FunctionEnterEvent(
            *[s[p] for p in ["file", "line", "id", "function_id", "function"]]
        )


class FunctionExitEvent(Event):
    def __init__(
        self,
        file: str,
        line: int,
        id_: int,
        function_id: int,
        function: str,
        return_value: Any = None,
        type_: str = None,
        tmp_var: str = None,
    ):
        super().__init__(file, line, id_, EventType.FUNCTION_EXIT)
        self.function = function
        self.function_id = function_id
        self.return_value = return_value
        self.type_ = type_
        self.tmp_var = tmp_var

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.file},{self.line},{self.id_},"
            f"{self.function},{self.return_value},{self.type_})"
        )

    def handle(self, model: Model):
        model.handle_function_exit_event(self)

    def serialize(self):
        default = super().serialize()
        default["function_id"] = self.function_id
        default["function"] = self.function
        return default

    def dump(self):
        return super().dump() + [
            self.function_id,
            self.function,
            self.return_value,
            self.type_,
        ]

    @staticmethod
    def deserialize(s: dict):
        assert all(p in s for p in ["file", "line", "id", "function_id", "function"])
        assert s["event_type"] == EventType.FUNCTION_EXIT.value
        return FunctionExitEvent(
            *[s[p] for p in ["file", "line", "id", "function_id", "function"]]
        )


class FunctionErrorEvent(Event):
    def __init__(self, file: str, line: int, id_: int, function_id: int, function: str):
        super().__init__(file, line, id_, EventType.FUNCTION_ERROR)
        self.function_id = function_id
        self.function = function

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.file},{self.line},{self.id_},"
            f"{self.function_id},{self.function})"
        )

    def handle(self, model: Model):
        model.handle_function_error_event(self)

    def serialize(self):
        default = super().serialize()
        default["function_id"] = self.function_id
        default["function"] = self.function
        return default

    def dump(self):
        return super().dump() + [self.function_id, self.function]

    @staticmethod
    def deserialize(s: dict):
        assert all(p in s for p in ["file", "line", "id", "function_id", "function"])
        assert s["event_type"] == EventType.FUNCTION_ERROR.value
        return FunctionErrorEvent(
            *[s[p] for p in ["file", "line", "id", "function_id", "function"]]
        )


class ConditionEvent(Event):
    def __init__(
        self,
        file: str,
        line: int,
        id_: int,
        condition: str,
        value: bool = None,
        tmp_var: str = None,
    ):
        super().__init__(file, line, id_, EventType.CONDITION)
        self.value = value
        self.condition = condition
        self.tmp_var = tmp_var

    def __repr__(self):
        return f"{self.__class__.__name__}({self.file},{self.line},{self.id_},{self.value},{self.condition})"

    def handle(self, model: Model):
        model.handle_condition_event(self)

    def serialize(self):
        default = super().serialize()
        default["condition"] = self.condition
        return default

    def dump(self):
        return super().dump() + [self.condition, 1 if self.value else 0]

    @staticmethod
    def deserialize(s: dict):
        assert all(p in s for p in ["file", "line", "id", "condition"])
        assert s["event_type"] == EventType.CONDITION.value
        return ConditionEvent(*[s[p] for p in ["file", "line", "id", "condition"]])


class LoopBeginEvent(Event):
    def __init__(self, file: str, line: int, id_: int, loop_id: int):
        super().__init__(file, line, id_, EventType.LOOP_BEGIN)
        self.loop_id = loop_id

    def handle(self, model: Model):
        model.handle_loop_begin_event(self)

    def serialize(self):
        default = super().serialize()
        default["loop_id"] = self.loop_id
        return default

    def dump(self):
        return super().dump() + [self.loop_id]

    @staticmethod
    def deserialize(s: dict):
        assert all(p in s for p in ["file", "line", "id", "loop_id"])
        assert s["event_type"] == EventType.LOOP_BEGIN.value
        return LoopBeginEvent(*[s[p] for p in ["file", "line", "id", "loop_id"]])


class LoopHitEvent(Event):
    def __init__(self, file: str, line: int, id_: int, loop_id: int):
        super().__init__(file, line, id_, EventType.LOOP_HIT)
        self.loop_id = loop_id

    def handle(self, model: Model):
        model.handle_loop_hit_event(self)

    def serialize(self):
        default = super().serialize()
        default["loop_id"] = self.loop_id
        return default

    def dump(self):
        return super().dump() + [self.loop_id]

    @staticmethod
    def deserialize(s: dict):
        assert all(p in s for p in ["file", "line", "id", "loop_id"])
        assert s["event_type"] == EventType.LOOP_HIT.value
        return LoopHitEvent(*[s[p] for p in ["file", "line", "id", "loop_id"]])


class LoopEndEvent(Event):
    def __init__(self, file: str, line: int, id_: int, loop_id: int):
        super().__init__(file, line, id_, EventType.LOOP_END)
        self.loop_id = loop_id

    def handle(self, model: Model):
        model.handle_loop_end_event(self)

    def serialize(self):
        default = super().serialize()
        default["loop_id"] = self.loop_id
        return default

    def dump(self):
        return super().dump() + [self.loop_id]

    @staticmethod
    def deserialize(s: dict):
        assert all(p in s for p in ["file", "line", "id", "loop_id"])
        assert s["event_type"] == EventType.LOOP_END.value
        return LoopEndEvent(*[s[p] for p in ["file", "line", "id", "loop_id"]])


class UseEvent(Event):
    def __init__(self, file: str, line: int, id_: int, var: str, var_id: int = None):
        super().__init__(file, line, id_, EventType.USE)
        self.var = var
        self.var_id = var_id

    def __repr__(self):
        return f"{self.__class__.__name__}({self.file},{self.line},{self.id_},{self.var},{self.var_id})"

    def handle(self, model: Model):
        model.handle_use_event(self)

    def serialize(self):
        default = super().serialize()
        default["var"] = self.var
        return default

    def dump(self):
        return super().dump() + [self.var, self.var_id]

    @staticmethod
    def deserialize(s: dict):
        assert all(p in s for p in ["file", "line", "id", "var"])
        assert s["event_type"] == EventType.USE.value
        return UseEvent(*[s[p] for p in ["file", "line", "id", "var"]])


def serialize(event: Event):
    return event.serialize()


event_mapping = {
    EventType.LINE: LineEvent,
    EventType.BRANCH: BranchEvent,
    EventType.DEF: DefEvent,
    EventType.USE: UseEvent,
    EventType.FUNCTION_ENTER: FunctionEnterEvent,
    EventType.FUNCTION_EXIT: FunctionExitEvent,
    EventType.FUNCTION_ERROR: FunctionErrorEvent,
    EventType.LOOP_BEGIN: LoopBeginEvent,
    EventType.LOOP_HIT: LoopHitEvent,
    EventType.LOOP_END: LoopEndEvent,
    EventType.CONDITION: ConditionEvent,
}


def deserialize(s: dict):
    assert "event_type" in s
    type_ = EventType(s["event_type"])
    return event_mapping[type_].deserialize(s)


def dump(path: str, events: List[Event]):
    with open(path, "w") as fp:
        writer = csv.writer(fp)
        for e in events:
            writer.writerow(e.dump())


def load_event(event_type: EventType, *args):
    if event_type == EventType.BRANCH:
        return BranchEvent(
            args[0], int(args[1]), int(args[2]), int(args[3]), int(args[4])
        )
    elif event_type == EventType.DEF:
        # noinspection PyBroadException
        try:
            return DefEvent(
                args[0],
                int(args[1]),
                int(args[2]),
                args[3],
                int(args[4]),
                pickle.loads(base64.b64decode(args[5])),
                args[6],
            )
        except:
            if args[5] == "True":
                return DefEvent(
                    args[0],
                    int(args[1]),
                    int(args[2]),
                    args[3],
                    int(args[4]),
                    True,
                    args[6],
                )
            elif args[5] == "False":
                return DefEvent(
                    args[0],
                    int(args[1]),
                    int(args[2]),
                    args[3],
                    int(args[4]),
                    False,
                    args[6],
                )
            else:
                return DefEvent(
                    args[0],
                    int(args[1]),
                    int(args[2]),
                    args[3],
                    int(args[4]),
                    None,
                    args[6],
                )
    elif event_type == EventType.USE:
        return UseEvent(args[0], int(args[1]), int(args[2]), args[3], int(args[4]))
    elif event_type == EventType.FUNCTION_ENTER:
        return FunctionEnterEvent(
            args[0], int(args[1]), int(args[2]), int(args[3]), args[4]
        )
    elif event_type == EventType.FUNCTION_EXIT:
        # noinspection PyBroadException
        try:
            return FunctionExitEvent(
                args[0],
                int(args[1]),
                int(args[2]),
                int(args[3]),
                args[4],
                pickle.loads(base64.b64decode(args[5])),
                args[6],
            )
        except:
            if args[5] == "True":
                return FunctionExitEvent(
                    args[0],
                    int(args[1]),
                    int(args[2]),
                    int(args[3]),
                    args[4],
                    True,
                    args[6],
                )
            elif args[5] == "False":
                return FunctionExitEvent(
                    args[0],
                    int(args[1]),
                    int(args[2]),
                    int(args[3]),
                    args[4],
                    False,
                    args[6],
                )
            else:
                return FunctionExitEvent(
                    args[0],
                    int(args[1]),
                    int(args[2]),
                    int(args[3]),
                    args[4],
                    None,
                    args[6],
                )
    elif event_type == EventType.FUNCTION_ERROR:
        return FunctionErrorEvent(
            args[0], int(args[1]), int(args[2]), int(args[3]), args[4]
        )
    elif event_type == EventType.CONDITION:
        return ConditionEvent(
            args[0], int(args[1]), int(args[2]), args[3], bool(int(args[4]))
        )
    elif event_type in [EventType.LOOP_BEGIN, EventType.LOOP_HIT, event_type.LOOP_END]:
        return event_mapping[event_type](
            args[0], int(args[1]), int(args[2]), int(args[3])
        )
    else:
        return event_mapping[event_type](args[0], int(args[1]), int(args[2]))


def load(path) -> List[Event]:
    events = list()
    with open(path, "r") as fp:
        reader = csv.reader(fp)
        for row in reader:
            events.append(load_event(EventType(int(row[0])), *row[1:]))
    return events


def load_json(path) -> List[Event]:
    with open(path, "r") as fp:
        events = json.load(fp)
    return list(map(deserialize, events))
