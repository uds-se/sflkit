import atexit
import os
from pathlib import Path

from sflkitlib.events import EventType

from sflkit import instrument_config, Config
from utils import BaseTest


class TestInstrumentation(BaseTest):
    def _test_complex_structure(self, config: Config):
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

    def test_complex_structure_exclude(self):
        self._test_complex_structure(
            Config.create(
                path=os.path.join(BaseTest.TEST_RESOURCES, "test_instrumentation"),
                language="python",
                events="line",
                predicates="line",
                working=BaseTest.TEST_DIR,
                exclude=r"exclude_dir,exclude\.py,excluded_file,"
                + os.path.join("package", r"exclude.py"),
            )
        )

    def test_complex_structure_include(self):
        self._test_complex_structure(
            Config.create(
                path=os.path.join(BaseTest.TEST_RESOURCES, "test_instrumentation"),
                language="python",
                events="line",
                predicates="line",
                working=BaseTest.TEST_DIR,
                include=r"package,main\.py",
                exclude=os.path.join("package", r"exclude\.py"),
            )
        )

    def test_mapping_output(self):
        instrument_config(
            Config.create(
                path=os.path.join(BaseTest.TEST_RESOURCES, "test_instrumentation"),
                language="python",
                events="line",
                predicates="line",
                working=BaseTest.TEST_DIR,
                mapping_path="mapping.json",
            )
        )
        mapping = Path("mapping.json")
        self.assertTrue(mapping.exists())
        self.assertTrue(mapping.is_file())

    def test_instrument_exclude(self):
        src = Path(BaseTest.TEST_RESOURCES, "test_exclude")
        dst = Path(BaseTest.TEST_DIR)
        instrument_config(
            Config.create(
                path=str(src),
                language="python",
                events="line",
                predicates="line",
                working=BaseTest.TEST_DIR,
                include="included",
                exclude=os.path.join("included", "excluded"),
            )
        )
        included = dst / "included"
        excluded = included / "excluded"
        a = included / "a.py"
        b = excluded / "b.py"
        c = dst / "c.py"

        included_src = src / "included"
        excluded_src = included_src / "excluded"
        a_src = included_src / "a.py"
        b_src = excluded_src / "b.py"
        c_src = src / "c.py"

        self.assertTrue(included.exists())
        self.assertTrue(included.is_dir())
        self.assertTrue(excluded.exists())
        self.assertTrue(excluded.is_dir())
        self.assertTrue(a.exists())
        self.assertTrue(a.is_file())
        self.assertTrue(b.exists())
        self.assertTrue(b.is_file())
        self.assertTrue(c.exists())
        self.assertTrue(c.is_file())

        with open(a, "r") as fp:
            a_content = fp.read()
        with open(a_src, "r") as fp:
            a_src_content = fp.read()
        self.assertNotEqual(a_src_content, a_content)

        with open(b, "r") as fp:
            b_content = fp.read()
        with open(b_src, "r") as fp:
            b_src_content = fp.read()
        self.assertEqual(b_src_content, b_content)

        with open(c, "r") as fp:
            c_content = fp.read()
        with open(c_src, "r") as fp:
            c_src_content = fp.read()
        self.assertEqual(c_src_content, c_content)


class TestLib(BaseTest):
    @classmethod
    def setUpClass(cls) -> None:
        from sflkitlib import lib

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

    def tearDown(self) -> None:
        # noinspection PyBroadException
        try:
            os.remove(self.TEST_PATH)
        except:
            pass
        self.lib.reset()

    def test_get_id(self):
        x = 10
        self.assertEqual(id(x), self.lib.get_id(x))

    def test_get_type(self):
        x = 10
        self.assertEqual(type(x), self.lib.get_type(x))
