import json
import os

from sflkit import Config
from sflkit.analysis.analysis_type import AnalysisType
from sflkit.analysis.spectra import Spectrum
from sflkit.analysis.suggestion import Location
from sflkit.cli import main, parse_args
from utils import BaseTest


class TestCli(BaseTest):
    def setUp(self) -> None:
        self.config_path = f"test_config_{abs(hash(self))}.ini"
        self.results_path = f"results_{abs(hash(self))}.json"
        config = Config.create(
            path=os.path.join(BaseTest.TEST_RESOURCES, self.TEST_LINES),
            language="python",
            events="line",
            predicates="line",
            failing=os.path.join("test_dir", "EVENTS_PATH_0"),
            working=BaseTest.TEST_DIR,
        )
        Config.write(config, self.config_path)

    def tearDown(self) -> None:
        try:
            os.remove(self.config_path)
        except IOError:
            pass
        try:
            os.remove(self.results_path)
        except IOError:
            pass

    def test_instrument_analyze(self):
        main(parse_args(["-c", self.config_path, "instrument"]))
        self.execute_subject([], 0)
        main(parse_args(["-c", self.config_path, "analyze", "-o", self.results_path]))
        with open(self.results_path, "r") as fp:
            results = json.load(fp)
        self.assertEqual(1, len(results))
        name = AnalysisType.LINE.name
        self.assertIn(name, results)
        metrics = results[name]
        self.assertEqual(1, len(metrics))
        name = Spectrum.Ochiai.__name__
        self.assertIn(name, metrics)
        suggestions = metrics[name]
        self.assertEqual(1, len(suggestions))
        self.assertAlmostEqual(1, suggestions[0]["suspiciousness"], delta=self.DELTA)
        locations = suggestions[0]["locations"]
        self.assertEqual(3, len(locations))
        self.assertIn(repr(Location(self.ACCESS, 1)), locations)
        self.assertIn(repr(Location(self.ACCESS, 2)), locations)
        self.assertIn(repr(Location(self.ACCESS, 3)), locations)
