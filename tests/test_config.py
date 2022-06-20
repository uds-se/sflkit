import unittest

from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.factory import DefUseFactory
from sflkit.events import EventType
from sflkit.language.language import Language
from sflkit.language.python.factory import LineEventFactory, BranchEventFactory
from tests.utils import get_config


class ConfigTests(unittest.TestCase):

    def test_config(self):
        config = get_config('test/path', 'Python', 'Line,Branch', None,
                            'instrumentation/path', 'test,test2', None)
        self.assertEqual('test/path', config.target_path)
        self.assertEqual(Language.PYTHON, config.language)
        self.assertEqual(2, len(config.events))
        self.assertIn(EventType.LINE, config.events)
        self.assertIn(EventType.BRANCH, config.events)
        self.assertEqual(0, len(config.predicates))
        self.assertEqual(2, len(config.meta_visitor.visitors))
        self.assertTrue(any(map(lambda v: isinstance(v, LineEventFactory), config.meta_visitor.visitors)))
        self.assertTrue(any(map(lambda v: isinstance(v, BranchEventFactory), config.meta_visitor.visitors)))
        self.assertEqual('instrumentation/path', config.instrument_working)
        self.assertEqual(2, len(config.instrument_exclude))
        self.assertIn('test', config.instrument_exclude)
        self.assertIn('test2', config.instrument_exclude)
        self.assertIsNone(config.runner)

    def test_overwrite_predicates(self):
        config = get_config('test/path', 'Python', 'Line,Branch', 'Def_Use',
                            'instrumentation/path', None, None)
        self.assertEqual('test/path', config.target_path)
        self.assertEqual(Language.PYTHON, config.language)
        self.assertEqual(2, len(config.events))
        self.assertIn(EventType.DEF, config.events)
        self.assertIn(EventType.USE, config.events)
        self.assertEqual(1, len(config.predicates))
        self.assertIn(AnalysisType.DEF_USE, config.predicates)
        self.assertEqual(1, len(config.factory.factories))
        self.assertIsInstance(config.factory.factories[0], DefUseFactory)
        self.assertEqual('instrumentation/path', config.instrument_working)
        self.assertEqual(0, len(config.instrument_exclude))
        self.assertIsNone(config.runner)
