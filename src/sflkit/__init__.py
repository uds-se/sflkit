from sflkit.analysis.analyzer import Analyzer
from sflkit.analysis.predicate import Predicate
from sflkit.config import Config, parse_config
from sflkit.instrumentation.dir_instrumentation import DirInstrumentation

__version__ = "0.1.0"


def instrument_config(conf: Config, event_dump: str = None):
    instrumentation = DirInstrumentation(conf.visitor)
    instrumentation.instrument(
        conf.target_path,
        conf.instrument_working,
        suffixes=conf.language.suffixes,
        excludes=conf.instrument_exclude,
    )
    if event_dump:
        instrumentation.dump_events(event_dump)


def instrument(config_path: str, event_dump: str = None):
    conf = parse_config(config_path)
    instrument_config(conf, event_dump)


def analyze_config(conf: Config, analysis_dump: str = None):
    analyzer = Analyzer(conf.failing, conf.passing, conf.factory)
    analyzer.analyze()
    if analysis_dump:
        analyzer.dump(analysis_dump)
    results = dict()
    for analysis_type in conf.predicates:
        results[analysis_type.name] = dict()
        for metric in conf.metrics:
            try:
                results[analysis_type.name][
                    metric.__name__
                ] = analyzer.get_sorted_suggestions(
                    conf.target_path, metric, analysis_type
                )
            except (AttributeError, ValueError, TypeError) as e:
                raise e
    return results


def analyze(config_path: str, analysis_dump: str = None):
    conf = parse_config(config_path)
    return analyze_config(conf, analysis_dump)


__all__ = [
    "analysis",
    "events",
    "instrument",
    "language",
    "model",
    "runners",
    "config",
    "instrument",
    "instrument_config",
    "analyze",
    "analyze_config",
    "Analyzer",
    "Config",
]
