import os
import shutil
import subprocess
import unittest

from sflkit import instrument_config
from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.analyzer import Analyzer
from sflkit.analysis.predicate import Condition, Branch
from sflkit.analysis.spectra import Line, Spectrum
from sflkit.analysis.suggestion import Location
from sflkit.model.event_file import EventFile
from sflkit.config import Config

test_resources = os.path.join('..', 'resources', 'subjects', 'tests')
test_dir = 'test_dir'
test_events = 'test_events.json'
test_path = 'EVENTS_PATH'
python = 'python3.9'
access = 'main.py'


class EventTests(unittest.TestCase):

    def test_lines_relevant(self):
        config = Config.config(path=os.path.join(test_resources, 'test_lines'), language='python', events='line',
                               predicates='line', working=test_dir)
        instrument_config(config)

        subprocess.run([python, access], cwd=test_dir)

        event_file = EventFile(os.path.join(test_dir, test_path), 0, True)

        analyzer = Analyzer([event_file], [], config.factory)
        analyzer.analyze()
        predicates = analyzer.get_analysis()
        line = False
        for p in predicates:
            self.assertIsInstance(p, Line)
            line = True
            self.assertEqual(1, p.qe(), f'qe is wrong for {p}')
        self.assertTrue(line)

    def test_lines_irrelevant(self):
        config = Config.config(path=os.path.join(test_resources, 'test_lines'), language='python', events='line',
                               predicates='line', working=test_dir)
        instrument_config(config)

        subprocess.run([python, access], cwd=test_dir)

        event_file = EventFile(os.path.join(test_dir, test_path), 0, True)

        analyzer = Analyzer([], [event_file], config.factory)
        analyzer.analyze()
        predicates = analyzer.get_analysis()
        line = False
        for p in predicates:
            self.assertIsInstance(p, Line)
            line = True
            self.assertEqual(0, p.qe(), f'qe is wrong for {p}')
        self.assertTrue(line)

    def test_branches_relevant(self):
        config = Config.config(path=os.path.join(test_resources, 'test_branches'), language='python', events='branch',
                               predicates='line,branch,condition', working=test_dir)
        instrument_config(config)

        subprocess.run([python, access], cwd=test_dir)

        event_file = EventFile(os.path.join(test_dir, test_path), 0, True)

        analyzer = Analyzer([event_file], [], config.factory)
        analyzer.analyze()
        predicates = analyzer.get_analysis()
        line, condition, branch = False, False, False
        for p in predicates:
            if isinstance(p, Line):
                self.assertEqual(1, p.get_metric(Spectrum.qe), f'qe is wrong for {p}')
                line = True
            elif isinstance(p, Condition):
                self.assertEqual(1, p.get_metric(Spectrum.qe), f'qe is wrong for {p}')
                condition = True
            elif isinstance(p, Branch):
                if p.passed_observed or p.failed_observed:
                    self.assertEqual(1, p.get_metric(Spectrum.qe), f'qe is wrong for {p}')
                    branch = True
                else:
                    self.assertEqual(0, p.get_metric(Spectrum.qe), f'qe is wrong for {p}')
        self.assertTrue(line and condition and branch)

    def test_branches_irrelevant(self):
        config = Config.config(path=os.path.join(test_resources, 'test_branches'), language='python', events='branch',
                               predicates='line,branch,condition', working=test_dir)
        instrument_config(config)

        subprocess.run([python, access], cwd=test_dir)

        event_file = EventFile(os.path.join(test_dir, test_path), 0, True)

        analyzer = Analyzer([], [event_file], config.factory)
        analyzer.analyze()
        predicates = analyzer.get_analysis()
        line, condition, branch = False, False, False
        for p in predicates:
            if isinstance(p, Line):
                self.assertEqual(p.get_metric(Spectrum.qe), 0, f'qe is wrong for {p}')
                line = True
            elif isinstance(p, Condition):
                self.assertEqual(p.get_metric(Spectrum.qe), 0, f'qe is wrong for {p}')
                condition = True
            elif isinstance(p, Branch):
                self.assertEqual(p.get_metric(Spectrum.qe), 0, f'qe is wrong for {p}')
                branch = True
        self.assertTrue(line and condition and branch)


class SuggestionsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        original_dir = os.path.join(test_resources, 'test_suggestions')
        config = Config.config(original_dir, language='python', events='branch',
                               predicates='line,branch,def_use', working=test_dir)
        instrument_config(config)

        subprocess.run([python, access, '2', '1', '3'], cwd=test_dir)
        shutil.move(os.path.join(test_dir, test_path), os.path.join(test_dir, test_path + '_1'))
        event_file_1 = EventFile(os.path.join(test_dir, test_path + '_1'), 0, True)

        subprocess.run([python, access, '3', '2', '1'], cwd=test_dir)
        shutil.move(os.path.join(test_dir, test_path), os.path.join(test_dir, test_path + '_2'))
        event_file_2 = EventFile(os.path.join(test_dir, test_path + '_2'), 1, False)

        subprocess.run([python, access, '3', '1', '2'], cwd=test_dir)
        shutil.move(os.path.join(test_dir, test_path), os.path.join(test_dir, test_path + '_3'))
        event_file_3 = EventFile(os.path.join(test_dir, test_path + '_3'), 2, False)

        analyzer = Analyzer([event_file_1], [event_file_2, event_file_3], config.factory)
        analyzer.analyze()
        cls.analyzer = analyzer
        cls.original_dir = original_dir

    def test_line_suggestions(self):
        predicates = self.analyzer.get_analysis_by_type(AnalysisType.LINE)
        suggestions = sorted(map(lambda p: p.get_suggestion(), predicates))
        self.assertEqual(1, suggestions[-1].suspiciousness)
        self.assertEqual(1, len(suggestions[-1].lines))
        self.assertEqual(Location('main.py', 10), suggestions[-1].lines[0])

    def test_def_use_suggestions(self):
        predicates = self.analyzer.get_analysis_by_type(AnalysisType.DEF_USE)
        suggestions = sorted(map(lambda p: p.get_suggestion(), predicates))
        self.assertEqual(1, suggestions[-1].suspiciousness)
        self.assertEqual(2, len(suggestions[-1].lines))
        self.assertIn(Location('main.py', 10), suggestions[-1].lines)

    def test_branch_suggestions(self):
        predicates = self.analyzer.get_analysis_by_type(AnalysisType.BRANCH)
        suggestions = sorted(map(lambda p: p.get_suggestion(base_dir=self.original_dir), predicates))
        self.assertEqual(0.5, suggestions[-1].suspiciousness)
        self.assertEqual(2, len(suggestions[-1].lines))
        self.assertIn(Location('main.py', 10), suggestions[-1].lines)
