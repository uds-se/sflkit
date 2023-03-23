import os
from typing import List

from sflkit import Config, instrument_config
from sflkit.events import EventType
from sflkit.events.event import (
    LineEvent,
    Event,
    load_json,
    BranchEvent,
    DefEvent,
    UseEvent,
    ConditionEvent,
    FunctionEnterEvent,
    FunctionExitEvent,
    FunctionErrorEvent,
    LoopBeginEvent,
    LoopHitEvent,
    LoopEndEvent,
)
from sflkit.language.language import Language
from utils import BaseTest


class LanguageTests(BaseTest):
    def test_python_equals_python3(self):
        self.assertEqual(Language.PYTHON, Language.PYTHON3)

    def _instrument(self, events: List[EventType]) -> List[Event]:
        config = Config.create(
            path=os.path.join(self.TEST_RESOURCES, "test_language"),
            language="python",
            events=",".join(e.name.lower() for e in events),
            working=BaseTest.TEST_DIR,
        )
        instrument_config(config, self.TEST_EVENTS)

        return load_json(self.TEST_EVENTS)

    def _verify_events(self, actual, expected):
        for e in expected:
            self.assertIn(e, actual)
        self.assertEqual(len(expected), len(actual))

    def setUp(self) -> None:
        self.counter = 0

    def _count(self) -> int:
        self.counter += 1
        return self.counter - 1

    def test_language_complex_lines(self):
        self._verify_events(
            self._instrument([EventType.LINE]),
            list(
                LineEvent(self.ACCESS, line, self._count())
                for line in [
                    2,
                    4,
                    5,
                    10,
                    13,
                    17,
                    21,
                    24,
                    25,
                    26,
                    28,
                    29,
                    31,
                    32,
                    34,
                    35,
                    37,
                    38,
                    40,
                    41,
                    43,
                    44,
                    48,
                    51,
                    52,
                    54,
                    55,
                    59,
                    62,
                    63,
                    65,
                    68,
                    69,
                    70,
                    72,
                    73,
                ]
            ),
        )

    def test_language_complex_branches(self):
        self._verify_events(
            self._instrument([EventType.BRANCH]),
            list(
                BranchEvent(self.ACCESS, line, self._count(), 0, 1)
                for line, then_id, else_id in [
                    (34, 0, 1),
                    (34, 1, 0),
                    (37, 2, 3),
                    (37, 3, 2),
                    (40, 4, 5),
                    (40, 5, 4),
                    (62, 6, -1),
                    (64, 6, -1),
                    (72, 7, 8),
                    (72, 8, 7),
                ]
            ),
        )

    def test_language_complex_def(self):
        self._verify_events(
            self._instrument([EventType.DEF]),
            list(
                DefEvent(self.ACCESS, line, self._count(), var)
                for line, var in [
                    (12, "exc_type"),
                    (12, "exc_val"),
                    (12, "exc_tb"),
                    (16, "x"),
                    (16, "y"),
                    (20, "x"),
                    (20, "y"),
                    (20, "z"),
                    (24, "t"),
                    (25, "n"),
                    (26, "o"),
                    (28, "a"),
                    (31, "a"),
                    (37, "i"),
                    (40, "i"),
                    (48, "x"),
                    (52, "x"),
                    (69, "m"),
                    (70, "m"),
                ]
            ),
        )

    def test_language_complex_use(self):
        self._verify_events(
            self._instrument([EventType.USE]),
            list(
                UseEvent(self.ACCESS, line, self._count(), var)
                for line, var in [
                    (4, "future"),
                    (4, "future.__version__"),
                    (4, "print"),
                    (5, "digits"),
                    (5, "print"),
                    (10, "self"),
                    (17, "x"),
                    (17, "y"),
                    (21, "x"),
                    (21, "y"),
                    (21, "z"),
                    (25, "t"),
                    (25, "bar"),
                    (28, "A"),
                    (29, "n"),
                    (29, "t"),
                    (29, "o"),
                    (29, "a"),
                    (29, "a.foo"),
                    (31, "A"),
                    (32, "a"),
                    (32, "a.foo"),
                    (37, "range"),
                    (40, "range"),
                    (43, "a"),
                    (44, "n"),
                    (51, "x"),
                    (52, "x"),
                    (54, "f"),
                    (55, "x"),
                    (59, "ValueError"),
                    (63, "foo"),
                    (70, "m"),
                    (72, "m"),
                    (73, "m"),
                    (73, "print"),
                ]
            ),
        )

    def test_language_complex_condition(self):
        self._verify_events(
            self._instrument([EventType.CONDITION]),
            list(
                ConditionEvent(self.ACCESS, line, self._count(), condition)
                for line, condition in [
                    (34, "True"),
                    (72, "False"),
                    (72, "not False"),
                    (72, "m"),
                    (72, "not False or m"),
                ]
            ),
        )

    def test_language_complex_function_enter(self):
        self._verify_events(
            self._instrument(
                [
                    EventType.FUNCTION_ENTER,
                ]
            ),
            list(
                FunctionEnterEvent(self.ACCESS, line, self._count(), id_, function)
                for line, id_, function in [
                    (9, 0, "__enter__"),
                    (12, 1, "__exit__"),
                    (16, 2, "foo"),
                    (20, 3, "bar"),
                    (47, 4, "baz"),
                    (50, 5, "f"),
                    (58, 6, "foo"),
                ]
            ),
        )

    def test_language_complex_function_exit(self):
        self._verify_events(
            self._instrument(
                [
                    EventType.FUNCTION_EXIT,
                ]
            ),
            list(
                FunctionExitEvent(self.ACCESS, line, self._count(), id_, function)
                for line, id_, function in [
                    (9, 0, "__enter__"),
                    (10, 0, "__enter__"),
                    (12, 1, "__exit__"),
                    (16, 2, "foo"),
                    (17, 2, "foo"),
                    (20, 3, "bar"),
                    (21, 3, "bar"),
                    (47, 4, "baz"),
                    (50, 5, "f"),
                    (55, 4, "baz"),
                    (58, 6, "foo"),
                ]
            ),
        )

    def test_language_complex_function_error(self):
        self._verify_events(
            self._instrument(
                [
                    EventType.FUNCTION_ERROR,
                ]
            ),
            list(
                FunctionErrorEvent(self.ACCESS, line, self._count(), id_, function)
                for line, id_, function in [
                    (9, 0, "__enter__"),
                    (12, 1, "__exit__"),
                    (16, 2, "foo"),
                    (20, 3, "bar"),
                    (47, 4, "baz"),
                    (50, 5, "f"),
                    (58, 6, "foo"),
                ]
            ),
        )

    def test_language_complex_loop_begin(self):
        self._verify_events(
            self._instrument(
                [
                    EventType.LOOP_BEGIN,
                    EventType.LOOP_HIT,
                    EventType.LOOP_END,
                ]
            ),
            sum(
                [
                    [
                        LoopBeginEvent(self.ACCESS, line, self._count(), id_),
                        LoopHitEvent(self.ACCESS, line, self._count(), id_),
                        LoopEndEvent(self.ACCESS, line, self._count(), id_),
                    ]
                    for line, id_ in [
                        (34, 0),
                        (37, 1),
                        (40, 2),
                    ]
                ],
                start=[],
            ),
        )
