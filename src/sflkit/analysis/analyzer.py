import os
from typing import List, Callable, Set, Dict

from sflkit.analysis.analysis_type import AnalysisType, AnalysisObject
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
        self.paths: Dict[int, os.PathLike] = dict()
        self.max_suspiciousness = 0
        self.min_suspiciousness = 0
        self.avg_suspiciousness = 0

    def _analyze(self, event_file):
        self.model.prepare(event_file)
        with event_file:
            for event in event_file.load():
                event.handle(self.model)

    def _finalize(self):
        self.model.finalize(self.irrelevant_event_files, self.relevant_event_files)

    def analyze(self):
        for event_file in self.relevant_event_files + self.irrelevant_event_files:
            self.paths[event_file.run_id] = event_file.path
            self._analyze(event_file)
        self._finalize()

    def dump(self, path):
        pass

    def get_analysis(self) -> Set[AnalysisObject]:
        return list(self.model.get_analysis())

    def get_analysis_by_type(self, type_: AnalysisType) -> Set[AnalysisObject]:
        return list(
            filter(lambda p: p.analysis_type() == type_, self.model.get_analysis())
        )

    def get_sorted_suggestions(
        self, base_dir, metric: Callable = None, type_: AnalysisType = None
    ) -> List[Suggestion]:
        if type_:
            objects = self.get_analysis_by_type(type_)
        else:
            objects = self.get_analysis()
        return self.get_sorted_suggestions_from_analysis(base_dir, objects, metric)

    def get_sorted_suggestions_from_analysis(
        self, base_dir, analysis: Set[AnalysisObject], metric: Callable = None
    ) -> List[Suggestion]:
        suggestions = dict()
        max_suspiciousness = float("-inf")
        min_suspiciousness = float("inf")
        avg_suspiciousness = 0
        for suggestion in map(
            lambda p: p.get_suggestion(metric=metric, base_dir=base_dir), analysis
        ):
            max_suspiciousness = max(max_suspiciousness, suggestion.suspiciousness)
            min_suspiciousness = min(min_suspiciousness, suggestion.suspiciousness)
            avg_suspiciousness += suggestion.suspiciousness
            if suggestion.suspiciousness not in suggestions:
                suggestions[suggestion.suspiciousness] = set(suggestion.lines)
            else:
                suggestions[suggestion.suspiciousness] |= set(suggestion.lines)

        self.max_suspiciousness = max_suspiciousness
        self.min_suspiciousness = min_suspiciousness
        self.avg_suspiciousness = avg_suspiciousness / len(analysis)

        return sorted(
            [
                Suggestion(list(lines), suspiciousness)
                for suspiciousness, lines in suggestions.items()
            ],
            reverse=True,
        )[:]

    def get_coverage_per_run(
        self, type_: AnalysisType = None
    ) -> Dict[EventFile, Set[AnalysisObject]]:
        if type_:
            objects = self.get_analysis_by_type(type_)
        else:
            objects = self.get_analysis()
        coverage = dict()
        for obj in objects:
            for run_id in obj.hits:
                if run_id not in coverage:
                    coverage[run_id] = {obj}
                else:
                    coverage[run_id].add(obj)
        return coverage

    def get_coverage(self, type_: AnalysisType = None) -> Set[AnalysisObject]:
        coverage = self.get_coverage_per_run(type_)
        return set.union(*coverage.values())
