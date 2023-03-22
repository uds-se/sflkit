import sys

sys.path = sys.path[1:] + sys.path[:1]
import atexit
import csv
import os
import pickle
import base64
from typing import Any

sys.path = sys.path[-1:] + sys.path[:-1]

from sflkit.events import event

_event_path_file = open(os.getenv("EVENTS_PATH", default="EVENTS_PATH"), "w")
_event_path_writer = csv.writer(_event_path_file)


def reset():
    # noinspection PyBroadException
    try:
        dump_events()
    except:
        pass
    global _event_path_file
    _event_path_file = open(os.getenv("EVENTS_PATH", default="EVENTS_PATH"), "w")
    global _event_path_writer
    _event_path_writer = csv.writer(_event_path_file)


def get_id(x: Any):
    try:
        return id(x)
    except (AttributeError, TypeError):
        return None


def get_type(x: Any):
    try:
        return type(x)
    except (AttributeError, TypeError):
        return None


def dump_events():
    _event_path_file.close()


atexit.register(dump_events)


def add_line_event(file: str, line: int, id_: int):
    _event_path_writer.writerow(event.LineEvent(file, line, id_).dump())


def add_branch_event(file: str, line: int, id_: int, then_id: int, else_id: int):
    _event_path_writer.writerow(
        event.BranchEvent(file, line, id_, then_id, else_id).dump()
    )


def add_def_event(
    file: str, line: int, id_: int, var: str, var_id: int, value: Any, type_: type
):
    if var_id is not None:
        if (
            type_ in [int, float, complex, str, bytes, bytearray, memoryview, bool]
            or value is None
        ):
            _event_path_writer.writerow(
                event.DefEvent(
                    file,
                    line,
                    id_,
                    var,
                    var_id,
                    base64.b64encode(pickle.dumps(value)).decode("utf8"),
                    type_.__name__,
                ).dump()
            )
        else:
            _event_path_writer.writerow(
                event.DefEvent(
                    file,
                    line,
                    id_,
                    var,
                    var_id,
                    var_id,
                    f"{type_.__module__}.{type_.__name__}",
                ).dump()
            )


def add_function_enter_event(
    file: str, line: int, id_: int, function_id: int, function: str
):
    _event_path_writer.writerow(
        event.FunctionEnterEvent(file, line, id_, function_id, function).dump()
    )


def add_function_exit_event(
    file: str,
    line: int,
    id_: int,
    function_id: int,
    function: str,
    return_value: Any,
    type_: type,
):
    if (
        type_ in [int, float, complex, str, bytes, bytearray, memoryview]
        or return_value is None
    ):
        _event_path_writer.writerow(
            event.FunctionExitEvent(
                file,
                line,
                id_,
                function_id,
                function,
                base64.b64encode(pickle.dumps(return_value)).decode("utf8"),
                type_.__name__,
            ).dump()
        )
    else:
        # noinspection PyBroadException
        try:
            _event_path_writer.writerow(
                event.FunctionExitEvent(
                    file,
                    line,
                    id_,
                    function_id,
                    function,
                    True if return_value else False,
                    type_.__name__,
                ).dump()
            )
        except:
            _event_path_writer.writerow(
                event.FunctionExitEvent(
                    file, line, id_, function_id, function, None, type_.__name__
                ).dump()
            )


def add_function_error_event(
    file: str, line: int, id_: int, function_id: int, function: str
):
    _event_path_writer.writerow(
        event.FunctionErrorEvent(file, line, id_, function_id, function).dump()
    )


def add_condition_event(file: str, line: int, id_: int, condition: str, value: Any):
    if value:
        _event_path_writer.writerow(
            event.ConditionEvent(file, line, id_, condition, True).dump()
        )
    else:
        _event_path_writer.writerow(
            event.ConditionEvent(file, line, id_, condition, False).dump()
        )


def add_loop_begin_event(file: str, line: int, id_: int, loop_id: int):
    _event_path_writer.writerow(event.LoopBeginEvent(file, line, id_, loop_id).dump())


def add_loop_hit_event(file: str, line: int, id_: int, loop_id: int):
    _event_path_writer.writerow(event.LoopHitEvent(file, line, id_, loop_id).dump())


def add_loop_end_event(file: str, line: int, id_: int, loop_id: int):
    _event_path_writer.writerow(event.LoopEndEvent(file, line, id_, loop_id).dump())


def add_use_event(file: str, line: int, id_: int, var: str, var_id: int):
    if var_id is not None:
        _event_path_writer.writerow(event.UseEvent(file, line, id_, var, var_id).dump())
