import os.path
import unittest

from sflkit import instrument, analyze
from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.factory import DefUseFactory
from sflkit.analysis.spectra import Spectrum
from sflkit.analysis.suggestion import Location
from sflkit.config import Config, write_config
from sflkit.events import EventType
from sflkit.language.language import Language
from sflkit.language.python.factory import LineEventFactory, BranchEventFactory
from utils import BaseTest


class ConfigTests(unittest.TestCase):
    def test_config(self):
        config = Config.create(
            path=os.path.join("test", "path"),
            language="Python",
            events="Line,Branch",
            working=os.path.join("instrumentation", "path"),
            exclude="test,test2",
        )
        self.assertEqual(os.path.join("test", "path"), config.target_path)
        self.assertEqual(Language.PYTHON, config.language)
        self.assertEqual(2, len(config.events))
        self.assertIn(EventType.LINE, config.events)
        self.assertIn(EventType.BRANCH, config.events)
        self.assertEqual(0, len(config.predicates))
        self.assertEqual(2, len(config.meta_visitor.visitors))
        self.assertTrue(
            any(
                map(
                    lambda v: isinstance(v, LineEventFactory),
                    config.meta_visitor.visitors,
                )
            )
        )
        self.assertTrue(
            any(
                map(
                    lambda v: isinstance(v, BranchEventFactory),
                    config.meta_visitor.visitors,
                )
            )
        )
        self.assertEqual(
            os.path.join("instrumentation", "path"), config.instrument_working
        )
        self.assertEqual(2, len(config.instrument_exclude))
        self.assertIn("test", config.instrument_exclude)
        self.assertIn("test2", config.instrument_exclude)
        self.assertIsNone(config.runner)

    def test_overwrite_predicates(self):
        config = Config.create(
            path=os.path.join("test", "path"),
            language="Python",
            events="Line,Branch",
            predicates="Def_Use",
            working=os.path.join("instrumentation", "path"),
        )
        self.assertEqual(os.path.join("test", "path"), config.target_path)
        self.assertEqual(Language.PYTHON, config.language)
        self.assertEqual(2, len(config.events))
        self.assertIn(EventType.DEF, config.events)
        self.assertIn(EventType.USE, config.events)
        self.assertEqual(1, len(config.predicates))
        self.assertIn(AnalysisType.DEF_USE, config.predicates)
        self.assertEqual(1, len(config.factory.factories))
        self.assertIsInstance(config.factory.factories[0], DefUseFactory)
        self.assertEqual(
            os.path.join("instrumentation", "path"), config.instrument_working
        )
        self.assertEqual(0, len(config.instrument_exclude))
        self.assertIsNone(config.runner)

    def test_create_config(self):
        config = Config.create(
            path=os.path.join("test", "path"),
            language="Python",
            events="Line,Branch",
            working=os.path.join("instrumentation", "path"),
            exclude="test,test2",
        )
        created_config = Config.create_from_values(
            config.target_path,
            config.language,
            config.predicates,
            config.factory,
            config.events,
            config.metrics,
            config.meta_visitor,
            config.visitor,
            config.passing,
            config.failing,
            config.instrument_exclude,
            config.instrument_working,
            config.runner,
        )
        self.assertEqual(config.target_path, created_config.target_path)
        self.assertEqual(config.language, created_config.language)
        self.assertEqual(config.predicates, created_config.predicates)
        self.assertEqual(config.factory, created_config.factory)
        self.assertEqual(config.events, created_config.events)
        self.assertEqual(config.metrics, created_config.metrics)
        self.assertEqual(config.meta_visitor, created_config.meta_visitor)
        self.assertEqual(config.visitor, created_config.visitor)
        self.assertEqual(config.passing, created_config.passing)
        self.assertEqual(config.failing, created_config.failing)
        self.assertEqual(config.instrument_exclude, created_config.instrument_exclude)
        self.assertEqual(config.instrument_working, created_config.instrument_working)
        self.assertEqual(config.runner, created_config.runner)


class UtilizeConfigTest(BaseTest):
    def setUp(self) -> None:
        self.config_path = f"test_config_{abs(hash(self))}.ini"
        config = Config.create(
            path=os.path.join(BaseTest.TEST_RESOURCES, self.TEST_LINES),
            language="python",
            events="line",
            predicates="line",
            passing="test_dir/EVENTS_PATH_0",
            failing="test_dir/EVENTS_PATH_1",
            working=BaseTest.TEST_DIR,
        )
        write_config(config, self.config_path)

    def tearDown(self) -> None:
        try:
            os.remove(self.config_path)
        except IOError:
            pass

    def test_config(self):
        instrument(self.config_path)
        self.execute_subject([], 0)
        self.execute_subject([], 1)
        results = analyze(self.config_path)
        self.assertEqual(1, len(results))
        name = AnalysisType.LINE.name
        self.assertIn(name, results)
        metrics = results[name]
        self.assertEqual(1, len(metrics))
        name = Spectrum.Ochiai.__name__
        self.assertIn(name, metrics)
        suggestions = metrics[name]
        self.assertEqual(1, len(suggestions))
        self.assertAlmostEqual(
            0.7071067811865475, suggestions[0].suspiciousness, delta=self.DELTA
        )
        self.assertEqual(3, len(suggestions[0]))
        self.assertIn(Location(self.ACCESS, 1), suggestions[0].lines)
        self.assertIn(Location(self.ACCESS, 2), suggestions[0].lines)
        self.assertIn(Location(self.ACCESS, 3), suggestions[0].lines)
