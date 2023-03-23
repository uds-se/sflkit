import os
from typing import List

from sflkit import Config, instrument_config
from sflkit.events import EventType
from sflkit.events.event import LineEvent, Event, load_json, BranchEvent, DefEvent
from sflkit.language.language import Language
from utils import BaseTest


class LanguageTests(BaseTest):
    def test_python_equals_python3(self):
        self.assertEqual(Language.PYTHON, Language.PYTHON3)

    def _instrument(self, events: List[EventType]) -> List[Event]:
        config = Config.config(
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
                    1,
                    2,
                    4,
                    5,
                    10,
                    13,
                    16,
                    20,
                    23,
                    24,
                    25,
                    27,
                    28,
                    30,
                    31,
                    33,
                    34,
                    36,
                    37,
                    39,
                    40,
                    42,
                    43,
                    47,
                    50,
                    51,
                    53,
                    54,
                    58,
                    61,
                    62,
                    64,
                    67,
                    68,
                    69,
                    71,
                    72,
                ]
            ),
        )

    def test_language_complex_branches(self):
        self._verify_events(
            self._instrument([EventType.BRANCH]),
            list(
                BranchEvent(self.ACCESS, line, self._count(), 0, 1)
                for line, then_id, else_id in [
                    (33, 0, 1),
                    (33, 1, 0),
                    (36, 2, 3),
                    (36, 3, 2),
                    (39, 4, 5),
                    (39, 5, 4),
                    (61, 6, -1),
                    (63, 6, -1),
                    (71, 7, 8),
                    (71, 8, 7),
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
                    (15, "x"),
                    (15, "y"),
                    (19, "x"),
                    (19, "y"),
                    (19, "z"),
                    (23, "t"),
                    (24, "n"),
                    (25, "o"),
                    (27, "a"),
                    (30, "a"),
                    (36, "i"),
                    (39, "i"),
                    (47, "x"),
                    (51, "x"),
                    (68, "m"),
                    (69, "m"),
                ]
            ),
        )
