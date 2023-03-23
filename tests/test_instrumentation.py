import atexit
import os
from pathlib import Path

from parameterized import parameterized

from sflkit import instrument_config, Config
from sflkit.events import event, EventType
from utils import BaseTest


class TestInstrumentation(BaseTest):
    def test_complex_structure(self):
        config = Config.create(
            path=os.path.join(BaseTest.TEST_RESOURCES, "test_instrumentation"),
            language="python",
            events="line",
            predicates="line",
            working=BaseTest.TEST_DIR,
            exclude="exclude_dir,exclude.py,excluded_file,"
            + os.path.join("package", "exclude.py"),
        )
        instrument_config(config)
        dst = Path(BaseTest.TEST_DIR)
        src = Path(BaseTest.TEST_RESOURCES, "test_instrumentation")
        main_py = dst / "main.py"
        exclude_py = dst / "exclude.py"
        file = dst / "file"
        exclude_file = dst / "exclude_file"
        exclude_dir = dst / "exclude_dir"
        exclude_dir_file = dst / "exclude_dir" / "file"
        package = dst / "package"
        package___init___py = dst / "package" / "__init__.py"
        package_exclude_py = dst / "package" / "exclude.py"
        package_test_py = dst / "package" / "test.py"

        src_main_py = src / "main.py"
        src_exclude_py = src / "exclude.py"
        src_file = src / "file"
        src_exclude_file = src / "exclude_file"
        src_exclude_dir_file = src / "exclude_dir" / "file"
        src_package___init___py = src / "package" / "__init__.py"
        src_package_exclude_py = src / "package" / "exclude.py"
        src_package_test_py = src / "package" / "test.py"

        exist_files = [
            main_py,
            exclude_py,
            file,
            exclude_file,
            exclude_dir_file,
            package___init___py,
            package_exclude_py,
            package_test_py,
        ]
        exist_dirs = [exclude_dir, package]

        for f in exist_files:
            self.assertTrue(f.exists())
            self.assertTrue(f.is_file())

        for d in exist_dirs:
            self.assertTrue(d.exists())
            self.assertTrue(d.is_dir())

        for d, s in [
            (exclude_py, src_exclude_py),
            (file, src_file),
            (exclude_file, src_exclude_file),
            (exclude_dir_file, src_exclude_dir_file),
            (package_exclude_py, src_package_exclude_py),
        ]:
            with open(d, "r") as fp:
                d_content = fp.read()
            with open(s, "r") as fp:
                s_content = fp.read()
            self.assertEqual(s_content, d_content, f"{d} has other content then {s}")

        for d, s in [
            (main_py, src_main_py),
            (package___init___py, src_package___init___py),
            (package_test_py, src_package_test_py),
        ]:
            with open(d, "r") as fp:
                d_content = fp.read()
            with open(s, "r") as fp:
                s_content = fp.read()
            self.assertNotEqual(
                s_content, d_content, f"{d} has the same content then {s}"
            )


class TestLib(BaseTest):
    @classmethod
    def setUpClass(cls) -> None:
        from sflkit.instrumentation import lib

        atexit.unregister(lib.dump_events)
        cls.lib = lib
        cls.event_type_map = {
            EventType.DEF: lib.add_def_event,
            EventType.USE: lib.add_use_event,
            EventType.LINE: lib.add_line_event,
            EventType.BRANCH: lib.add_branch_event,
            EventType.CONDITION: lib.add_condition_event,
            EventType.LOOP_BEGIN: lib.add_loop_begin_event,
            EventType.LOOP_HIT: lib.add_loop_hit_event,
            EventType.LOOP_END: lib.add_loop_end_event,
            EventType.FUNCTION_ENTER: lib.add_function_enter_event,
            EventType.FUNCTION_EXIT: lib.add_function_exit_event,
            EventType.FUNCTION_ERROR: lib.add_function_error_event,
        }

    def setUp(self) -> None:
        self.events = None

    def load(self) -> None:
        self.lib.dump_events()
        self.events = event.load(self.TEST_PATH)

    def tearDown(self) -> None:
        # noinspection PyBroadException
        try:
            os.remove(self.TEST_PATH)
        except:
            pass
        self.lib.reset()

    @parameterized.expand(map(lambda x: (str(x), x), BaseTest.EVENTS))
    def test_lib(self, _, e):
        args = e.dump()[1:]
        while "int" in args:
            args[args.index("int")] = int
        while "bool" in args:
            args[args.index("bool")] = bool
        while "none" in args:
            args[args.index("none")] = type(None)
        while "list" in args:
            args[args.index("list")] = list
        self.event_type_map[e.event_type](*args)
        self.load()
        self.assertEqual(1, len(self.events))
        self.assertIn(e, self.events)

    def test_get_id(self):
        x = 10
        self.assertEqual(id(x), self.lib.get_id(x))

    def test_get_type(self):
        x = 10
        self.assertEqual(type(x), self.lib.get_type(x))
