import json
import os
from pathlib import Path
from typing import Dict, Optional, Any

from sflkitlib.events.event import Event, load_json, EventEncoder, load

SFLKIT_PATH = Path.home() / ".sflkit"


class InstrumentationError(RuntimeError):
    pass


class EventMapping:
    def __init__(self, mapping: Dict[int, Event] = None):
        self.mapping = mapping or dict()

    def get(self, event_id) -> Optional[Event]:
        return self.mapping.get(event_id, None)

    @staticmethod
    def get_path(identifier: str):
        return SFLKIT_PATH / f"{identifier}.json"

    @staticmethod
    def load(config: Any):
        if not hasattr(config, "identifier"):
            raise InstrumentationError(f"Argument does not have an identifier")
        return EventMapping.load_from_file(config.identifier())

    @staticmethod
    def load_from_file(identifier: str):
        file = EventMapping.get_path(identifier)
        if file.exists():
            return EventMapping(load_json(file))
        else:
            raise InstrumentationError(
                f"Cannot find information about instrumentation of {identifier or file}"
            )

    def write(self, config):
        if not hasattr(config, "identifier"):
            raise InstrumentationError(f"Argument does not have an identifier")
        SFLKIT_PATH.mkdir(parents=True, exist_ok=True)
        file = self.get_path(config.identifier())
        with file.open("w") as fp:
            json.dump(list(self.mapping.values()), fp, cls=EventEncoder)

    def __len__(self):
        return len(self.mapping)

    def load_events(self, event_log: os.PathLike):
        return load(event_log, self.mapping)

    def sorted(self):
        return sorted(list(self.mapping.values()), key=lambda e: e.event_id)

    def __next__(self):
        return next(self.mapping)

    def __iter__(self):
        return iter(self.mapping)
