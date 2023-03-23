import os
import subprocess

from parameterized import parameterized

from sflkit import instrument_config
from sflkit.config import Config
from sflkit.events import event
from utils import BaseTest


class EventTests(BaseTest):
    def test_lines(self):
        config = Config.create(
            path=os.path.join(self.TEST_RESOURCES, self.TEST_LINES),
            language="python",
            events="line",
            working=self.TEST_DIR,
        )
        instrument_config(config)

        subprocess.run([self.PYTHON, self.ACCESS], cwd=self.TEST_DIR)

        events = event.load(os.path.join(self.TEST_DIR, self.TEST_PATH))
        self.assertEqual(3, len(events))
        for i, e in enumerate(events):
            self.assertIsInstance(e, event.LineEvent, f"{e} is not a line event")
            self.assertEqual(self.ACCESS, e.file, f"{e} has not correct file")
            self.assertEqual(i + 1, e.line, f"{e} has not correct line")

    def test_branches(self):
        config = Config.create(
            path=os.path.join(self.TEST_RESOURCES, self.TEST_BRANCHES),
            language="python",
            events="line,branch",
            working=self.TEST_DIR,
        )
        instrument_config(config)

        subprocess.run([self.PYTHON, self.ACCESS], cwd=self.TEST_DIR)

        events = event.load(os.path.join(self.TEST_DIR, self.TEST_PATH))
        self.assertEqual(5, len(events))
        lines = [1, 4, 5]
        line_i = 0
        first_branch = True
        branch_lines = [1, 4]
        branch_i = 0
        for e in events:
            if e.event_type == event.EventType.LINE:
                self.assertIsInstance(e, event.LineEvent, f"{e} is not a line event")
                self.assertEqual(self.ACCESS, e.file, f"{e} has not correct file")
                self.assertEqual(lines[line_i], e.line, f"{e} has not correct line")
                line_i += 1
            elif e.event_type == event.EventType.BRANCH:
                self.assertIsInstance(
                    e, event.BranchEvent, f"{e} is not a condition event"
                )
                self.assertEqual(self.ACCESS, e.file, f"{e} has not correct file")
                self.assertEqual(
                    branch_lines[branch_i], e.line, f"{e} has not correct line"
                )
                if first_branch:
                    self.assertGreater(
                        e.then_id, e.else_id, f"{e} has not correct branch ids"
                    )
                else:
                    self.assertLess(
                        e.then_id, e.else_id, f"{e} has not correct branch ids"
                    )
                first_branch = False
                branch_i += 1

    @staticmethod
    def _test_events(events):
        config = Config.create(
            path=os.path.join(BaseTest.TEST_RESOURCES, "test_events"),
            language="python",
            events=events,
            working=BaseTest.TEST_DIR,
        )
        instrument_config(config)

        subprocess.run([BaseTest.PYTHON, BaseTest.ACCESS], cwd=BaseTest.TEST_DIR)
        return event.load(os.path.join(BaseTest.TEST_DIR, BaseTest.TEST_PATH))

    def test_function(self):
        events = self._test_events("function_enter,function_exit")
        self.assertEqual(24, len(events))
        function_enter = list(
            zip(
                [9, 2, 9, 2, 5, 5, 5, 5, 5, 9, 2, 5],
                [
                    "a",
                    "__init__",
                    "a",
                    "__init__",
                    "a",
                    "a",
                    "a",
                    "a",
                    "a",
                    "a",
                    "__init__",
                    "a",
                ],
            )
        )
        function_enter_i = 0
        function_exit = list(
            zip(
                [2, 13, 2, 6, 6, 6, 6, 6, 13, 2, 6, 13],
                [
                    "__init__",
                    "a",
                    "__init__",
                    "a",
                    "a",
                    "a",
                    "a",
                    "a",
                    "a",
                    "__init__",
                    "a",
                    "a",
                ],
                [None, 0, None, 8, 12, 16, 20, 24, 24, None, 2, 2],
            )
        )
        function_exit_i = 0
        for e in events:
            if e.event_type == event.EventType.FUNCTION_ENTER:
                line, function = function_enter[function_enter_i]
                self.assertIsInstance(
                    e, event.FunctionEnterEvent, f"{e} is not a line event"
                )
                self.assertEqual(BaseTest.ACCESS, e.file, f"{e} has not correct file")
                self.assertEqual(line, e.line, f"{e} has not correct line")
                self.assertEqual(function, e.function, f"{e} has not correct function")
                function_enter_i += 1
            elif e.event_type == event.EventType.FUNCTION_EXIT:
                line, function, value = function_exit[function_exit_i]
                self.assertIsInstance(
                    e, event.FunctionExitEvent, f"{e} is not a line event"
                )
                self.assertEqual(BaseTest.ACCESS, e.file, f"{e} has not correct file")
                self.assertEqual(line, e.line, f"{e} has not correct line")
                self.assertEqual(function, e.function, f"{e} has not correct function")
                self.assertEqual(value, e.return_value, f"{e} has not correct function")
                function_exit_i += 1

    def test_branch(self):
        events = self._test_events("branch")
        self.assertEqual(12, len(events))
        branches = list(
            zip(
                [11, 16, 11, 11, 11, 11, 11, 11, 11, 11, 18, 25],
                [1, 1, -1, -1, -1, -1, -1, 1, -1, 1, -1, 0],
            )
        )
        branches_i = 0
        for e in events:
            if e.event_type == event.EventType.BRANCH:
                line, mod = branches[branches_i]
                self.assertIsInstance(e, event.BranchEvent, f"{e} is not a line event")
                self.assertEqual(BaseTest.ACCESS, e.file, f"{e} has not correct file")
                self.assertEqual(line, e.line, f"{e} has not correct line")
                if mod < 0:
                    self.assertLess(
                        e.then_id,
                        e.else_id,
                        f"{e} has not correct branch ids",
                    )
                elif mod > 0:
                    self.assertGreater(
                        e.then_id,
                        e.else_id,
                        f"{e} has not correct branch ids",
                    )
                else:
                    self.assertEqual(-1, e.else_id, f"{e} has not correct branch ids")
                    self.assertLessEqual(
                        0, e.then_id, f"{e} has not correct branch ids"
                    )
                branches_i += 1

    def test_loop(self):
        events = self._test_events("loop_begin,loop_hit,loop_end")
        self.assertEqual(12, len(events))
        expected_loop = [
            (event.EventType.LOOP_BEGIN, 11),
            (event.EventType.LOOP_END, 11),
            (event.EventType.LOOP_BEGIN, 11),
            (event.EventType.LOOP_HIT, 11),
            (event.EventType.LOOP_HIT, 11),
            (event.EventType.LOOP_HIT, 11),
            (event.EventType.LOOP_HIT, 11),
            (event.EventType.LOOP_HIT, 11),
            (event.EventType.LOOP_END, 11),
            (event.EventType.LOOP_BEGIN, 11),
            (event.EventType.LOOP_HIT, 11),
            (event.EventType.LOOP_END, 11),
        ]
        for e, expected in zip(events, expected_loop):
            type_, line = expected
            self.assertEqual(type_, e.event_type, f"{e} is not of type {type_}")
            self.assertIsInstance(
                e,
                event.event_mapping[type_],
                f"{e} is not a {event.event_mapping[type_]}",
            )
            self.assertEqual(BaseTest.ACCESS, e.file, f"{e} has not correct file")
            self.assertEqual(line, e.line, f"{e} has not correct line")
            # noinspection PyUnresolvedReferences
            self.assertEqual(0, e.loop_id, f"{e} has not correct loop id")

    def test_def_use(self):
        events = self._test_events("def,use")
        loop = [
            # loop
            (event.EventType.DEF, 11, "i", None),
            (event.EventType.USE, 12, "b", None),
            (event.EventType.USE, 12, "d", None),
            (event.EventType.USE, 12, "d.a", None),
            # A.a
            (event.EventType.DEF, 5, "b", None),
            (event.EventType.USE, 6, "self", None),
            (event.EventType.USE, 6, "self.b", None),
            (event.EventType.USE, 6, "b", None),
            (event.EventType.DEF, 12, "d.b", None),
        ]

        def get_a(b, c, result):
            return (
                [
                    # a
                    (event.EventType.DEF, 9, "b", b),
                    (event.EventType.DEF, 9, "c", c),
                    (event.EventType.USE, 10, "b", None),
                    (event.EventType.USE, 10, "A", None),
                    # A.__init__
                    (event.EventType.DEF, 2, "b", b),
                    (event.EventType.USE, 3, "b", None),
                    (event.EventType.DEF, 3, "self.b", b),
                    (event.EventType.DEF, 10, "d", None),
                    (event.EventType.USE, 11, "c", None),
                    (event.EventType.USE, 11, "range", None),
                ]
                + loop * c
                + [
                    (event.EventType.USE, 13, "d", result),
                    (event.EventType.USE, 13, "d.b", result),
                ]
            )

        expected_def_uses = (
            [(event.EventType.USE, 16, "a", None)]
            + get_a(0, 0, 0)
            + [
                (event.EventType.USE, 18, "a", None),
            ]
            + get_a(4, 5, 24)
            + get_a(1, 1, 2)
            + [
                (event.EventType.USE, 19, "print", None),
                (event.EventType.USE, 24, "ValueError", None),
                (event.EventType.USE, 26, "print", None),
            ]
        )
        self.assertEqual(len(expected_def_uses), len(events))  # defs + uses
        for e, expected in zip(events, expected_def_uses):
            type_, line, var, val = expected
            self.assertEqual(
                type_, e.event_type, f"{e} is not of type {type_}, expected {expected}"
            )
            self.assertIsInstance(
                e,
                event.event_mapping[type_],
                f"{e} is not a {event.event_mapping[type_]}, expected {expected}",
            )
            self.assertEqual(
                BaseTest.ACCESS,
                e.file,
                f"{e} has not correct file, expected {expected}",
            )
            self.assertEqual(
                line, e.line, f"{e} has not correct line, expected {expected}"
            )
            if isinstance(var, list):
                self.assertIn(
                    e.var, var, f"{e} has not correct var, expected {expected}"
                )
            else:
                self.assertEqual(
                    var, e.var, f"{e} has not correct var, expected {expected}"
                )
            if type_ == event.EventType.DEF and val:
                if isinstance(val, list):
                    self.assertIn(
                        e.value, val, f"{e} has not correct value, expected {expected}"
                    )
                else:
                    self.assertEqual(
                        val, e.value, f"{e} has not correct value, expected {expected}"
                    )

    def test_condition(self):
        events = self._test_events("condition")
        self.assertEqual(4, len(events))
        expected_conditions = [
            (event.EventType.CONDITION, 16, "a(0, 0)", False),
            (event.EventType.CONDITION, 18, "a(4, 5)", True),
            (event.EventType.CONDITION, 18, "a(1, 1)", True),
            (event.EventType.CONDITION, 18, "a(4, 5) and a(1, 1)", True),
        ]
        for e, expected in zip(events, expected_conditions):
            type_, line, exp, ev = expected
            self.assertEqual(e.event_type, type_, f"{e} is not of type {type_}")
            self.assertIsInstance(
                e,
                event.event_mapping[type_],
                f"{e} is not a {event.event_mapping[type_]}",
            )
            self.assertEqual(BaseTest.ACCESS, e.file, f"{e} has not correct file")
            self.assertEqual(line, e.line, f"{e} has not correct line")
            self.assertEqual(ev, e.value, f"{e} has not correct value")
            self.assertEqual(exp, e.condition, f"{e} has not correct condition")


class SerializeEventsTest(BaseTest):
    @parameterized.expand(map(lambda x: (str(x), x), BaseTest.EVENTS))
    def test_serialize(self, _, e):
        self.assertEqual(e, event.deserialize(event.serialize(e)))

    @parameterized.expand(map(lambda x: (str(x), x), BaseTest.EVENTS))
    def test_load(self, _, e):
        args = e.dump()[1:]
        if e.event_type == event.EventType.FUNCTION_EXIT:
            if e.return_value == 1:
                args[5] = b"\x80\x04K\x01."
            elif e.return_value is None:
                args[5] = "None"
            elif e.return_value:
                args[5] = "True"
            elif not e.return_value:
                args[5] = "False"
        elif e.event_type == event.EventType.DEF:
            if e.value == 1:
                args[5] = b"\x80\x04K\x01."
            elif e.value is None:
                args[5] = "None"
            elif e.value:
                args[5] = "True"
            elif not e.value:
                args[5] = "False"

        self.assertEqual(e, event.load_event(e.event_type, *args))
