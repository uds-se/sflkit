from typing import List, Callable

from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.factory import AnalysisFactory
from sflkit.analysis.suggestion import Suggestion
from sflkit.model.event_file import EventFile
from sflkit.model.model import Model


class Analyzer(object):
    def __init__(
        self,
        relevant_event_files: List[EventFile],
        irrelevant_event_files: List[EventFile],
        factory: AnalysisFactory,
    ):
        self.relevant_event_files = relevant_event_files
        self.irrelevant_event_files = irrelevant_event_files
        self.model = Model(factory)

    def _analyze(self, event_file):
        self.model.prepare(event_file)
        with event_file:
            for event in event_file.load():
                event.handle(self.model)

    def _finalize(self):
        self.model.finalize(self.irrelevant_event_files, self.relevant_event_files)

    def analyze(self):
        for event_file in self.relevant_event_files + self.irrelevant_event_files:
            self._analyze(event_file)
        self._finalize()

    def dump(self, path):
        pass

    def get_analysis(self):
        return list(self.model.get_analysis())

    def get_analysis_by_type(self, type_: AnalysisType):
        return list(
            filter(lambda p: p.analysis_type() == type_, self.model.get_analysis())
        )

    def get_sorted_suggestions(
        self, base_dir, metric: Callable = None, type_: AnalysisType = None
    ):
        if type_:
            objects = self.get_analysis_by_type(type_)
        else:
            objects = self.get_analysis()
        suggestions = dict()
        for suggestion in map(
            lambda p: p.get_suggestion(metric=metric, base_dir=base_dir), objects
        ):
            if suggestion.suspiciousness not in suggestions:
                suggestions[suggestion.suspiciousness] = set(suggestion.lines)
            else:
                suggestions[suggestion.suspiciousness] |= set(suggestion.lines)

        return sorted(
            [
                Suggestion(list(lines), suspiciousness)
                for suspiciousness, lines in suggestions.items()
            ],
            reverse=True,
        )[:]
