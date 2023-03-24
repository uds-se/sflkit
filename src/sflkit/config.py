import configparser
import csv
import os.path
import queue
from typing import List, Callable, Union

from sflkit.analysis.predicate import Predicate
from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.factory import (
    analysis_factory_mapping,
    CombinationFactory,
    AnalysisFactory,
)
from sflkit.analysis.mapping import analysis_mapping
from sflkit.analysis.spectra import Spectrum
from sflkit.events import EventType
from sflkit.language.language import Language
from sflkit.language.meta import (
    CombinationVisitor,
    IDGenerator,
    TmpGenerator,
    MetaVisitor,
)
from sflkit.language.visitor import ASTVisitor
from sflkit.model.event_file import EventFile
from sflkit.runners import RunnerType


class ConfigError(Exception):
    pass


class Config:
    """
    The basic entry of the config file to start sd tools. The config file follows this form:

    [target]
    path=/path/to/the/subject
    language=Python|C                       : The programming language used

    [events]
    events=Event(,Event)*                   : The events to investigate, overwritten by predicates.
    predicates=Predicate(,Predicate)*        : The predicates to investigate, overwrites events.
    metrics=Metric(,Metric)*                : The metrics used for investigation
    passing=/path(,path)*                   : The event files of passing runs, if a dir is provided
                                              all files inside the tree will be treated as event files
    failing=/path(,path)*                   : The event files of failing runs, if a dir is provided
                                              all files inside the tree will be treated as event files

    [instrumentation]
    path=/path/to/the/instrumented/subject
    exclude=file(,file)*                    : Files to exclude from the instrumentation, should be a python re pattern

    [test]
    runner=TestRunner                       : The testrunner class, None if no run needed
    """

    def __init__(self, path: Union[str, configparser.ConfigParser] = None):
        self.target_path = None
        self.language = None
        self.predicates = list()
        self.factory = None
        self.events = list()
        self.metrics = list()
        self.meta_visitor = None
        self.visitor = None
        self.passing = list()
        self.failing = list()
        self.instrument_exclude = list()
        self.instrument_working = None
        self.runner = None
        if path:
            if isinstance(path, configparser.ConfigParser):
                config = path
            else:
                config = configparser.ConfigParser()
                config.read(path)
            try:

                # target section
                target = config["target"]
                self.target_path = target["path"]
                self.language = Language[target["language"].upper()]
                self.language.setup()

                # events section
                events = config["events"]
                if "predicates" in events:
                    # get the predicates
                    self.predicates = list(
                        map(
                            lambda p: AnalysisType[p.upper()],
                            list(csv.reader([events["predicates"]]))[0],
                        )
                    )
                    self.factory = CombinationFactory(
                        list(
                            map(
                                lambda p: analysis_factory_mapping[p](), self.predicates
                            )
                        )
                    )
                    # get the events
                    self.events = {
                        e for p in self.predicates for e in analysis_mapping[p].events()
                    }
                else:
                    self.factory = CombinationFactory(list())
                    # get the events
                    self.events = list(
                        map(
                            lambda e: EventType[e.upper()],
                            list(csv.reader([events["events"]]))[0],
                        )
                    )

                self.meta_visitor = CombinationVisitor(
                    self.language,
                    IDGenerator(),
                    TmpGenerator(),
                    [self.language.meta_visitors[e] for e in self.events],
                )
                self.visitor = self.language.visitor(self.meta_visitor)

                if "metrics" in events:
                    self.metrics = list(
                        map(
                            lambda m: getattr(Predicate, m),
                            list(csv.reader([events["metrics"]]))[0],
                        )
                    )
                else:
                    self.metrics = [Spectrum.Ochiai]

                run_id_generator = IDGenerator()
                if "passing" in events:
                    self.passing = self.get_event_files(
                        list(csv.reader([events["passing"]]))[0],
                        run_id_generator,
                        False,
                    )
                if "failing" in events:
                    self.failing = self.get_event_files(
                        list(csv.reader([events["failing"]]))[0], run_id_generator, True
                    )
                # instrumentation section
                instrument = config["instrumentation"]
                if "exclude" in instrument:
                    self.instrument_exclude = list(csv.reader([instrument["exclude"]]))[
                        0
                    ]
                self.instrument_working = instrument["path"]

                # test section
                if "test" in config:
                    test = config["test"]
                    if "runner" in test and test["runner"] != "None":
                        self.runner = RunnerType[test["runner"].upper()]

            except KeyError as e:
                raise ConfigError(e)

    @staticmethod
    def create_from_values(
        target_path: str = None,
        language: Language = None,
        predicates: List[AnalysisType] = None,
        factory: AnalysisFactory = None,
        events: List[EventType] = None,
        metrics: List[Callable] = None,
        meta_visitor: MetaVisitor = None,
        visitor: ASTVisitor = None,
        passing: List[EventFile] = None,
        failing: List[EventFile] = None,
        instrument_exclude: List[str] = None,
        instrument_working: str = None,
        runner: RunnerType = None,
    ):
        conf = Config()
        conf.target_path = target_path
        conf.language = language
        if language:
            conf.language.setup()
        conf.predicates = predicates if predicates else list()
        conf.factory = factory
        conf.events = events if events else list()
        conf.metrics = metrics if metrics else list()
        conf.meta_visitor = meta_visitor
        conf.visitor = visitor
        conf.passing = passing if passing else list()
        conf.failing = failing if failing else list()
        conf.instrument_exclude = instrument_exclude if instrument_exclude else list()
        conf.instrument_working = instrument_working
        conf.runner = runner
        return conf

    @staticmethod
    def get_event_files(files, run_id_generator, failing):
        file_queue = queue.Queue()
        for f in files:
            file_queue.put(f)
        result = list()
        while not file_queue.empty():
            element = file_queue.get()
            if os.path.exists(element):
                if os.path.isdir(element):
                    for f in os.listdir(element):
                        file_queue.put(os.path.join(element, f))
                elif os.path.isfile(element) and not os.path.islink(element):
                    result.append(
                        EventFile(
                            element, run_id_generator.get_next_id(), failing=failing
                        )
                    )
            else:
                result.append(
                    EventFile(element, run_id_generator.get_next_id(), failing=failing)
                )
        return result

    @staticmethod
    def create(
        path=None,
        language=None,
        events=None,
        predicates=None,
        metrics=None,
        passing=None,
        failing=None,
        working=None,
        exclude=None,
        runner=None,
    ):
        conf = configparser.ConfigParser()
        conf["target"] = dict()
        conf["events"] = dict()
        conf["instrumentation"] = dict()
        conf["test"] = dict()

        if path:
            conf["target"]["path"] = path
        if language:
            conf["target"]["language"] = language
        if events:
            conf["events"]["events"] = events
        if predicates:
            conf["events"]["predicates"] = predicates
        if metrics:
            conf["events"]["metrics"] = metrics
        if passing:
            conf["events"]["passing"] = passing
        if failing:
            conf["events"]["failing"] = failing
        if working:
            conf["instrumentation"]["path"] = working
        if exclude:
            conf["instrumentation"]["exclude"] = exclude
        if runner:
            conf["test"]["runner"] = runner

        return Config(conf)

    def write(self, path):
        conf = configparser.ConfigParser()
        conf["target"] = dict()
        conf["events"] = dict()
        conf["instrumentation"] = dict()
        conf["test"] = dict()

        if self.target_path:
            conf["target"]["path"] = self.target_path
        if self.language:
            conf["target"]["language"] = self.language.name
        if self.events:
            conf["events"]["events"] = ",".join(e.name for e in self.events)
        if self.predicates:
            conf["events"]["predicates"] = ",".join(p.name for p in self.predicates)
        if self.metrics:
            conf["events"]["metrics"] = ",".join(m.__name__ for m in self.metrics)
        if self.passing:
            conf["events"]["passing"] = ",".join(e.path for e in self.passing)
        if self.failing:
            conf["events"]["failing"] = ",".join(e.path for e in self.failing)
        if self.instrument_working:
            conf["instrumentation"]["path"] = self.instrument_working
        if self.instrument_exclude:
            conf["instrumentation"]["exclude"] = ",".join(self.instrument_exclude)
        if self.runner:
            conf["test"]["runner"] = self.runner.name

        with open(path, "w") as fp:
            conf.write(fp)


def parse_config(path: str) -> Config:
    return Config(path)


def write_config(config: Config, path: str):
    config.write(path)
