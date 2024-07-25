import os
import sys
from typing import Optional, Union, List, Sequence

# noinspection PyPackageRequirements
from _pytest._code import ExceptionInfo

# noinspection PyPackageRequirements
from _pytest._io import TerminalWriter

# noinspection PyPackageRequirements
from _pytest.config import (
    ExitCode,
    _prepareconfig,
    ConftestImportFailure,
    UsageError,
    filter_traceback_for_conftest_import_failure,
    _PluggyPlugin,
)


def pytest_collection_finish(session):
    """
    Called after collection has been performed and modified.
    """
    file = os.getenv("SFLKIT_PYTEST_COLLECTION_FINISH_FILE", "tmp_sflkit_pytest")
    with open(file, "w") as f:
        for item in session.items:
            f.write(item.nodeid + "\n")


def main(
    args: Optional[Union[List[str], "os.PathLike[str]"]] = None,
    plugins: Optional[Sequence[Union[str, _PluggyPlugin]]] = None,
) -> Union[int, ExitCode]:
    """Perform an in-process test run.

    :param args: List of command line arguments.
    :param plugins: List of plugin objects to be auto-registered during initialization.

    :returns: An exit code.
    """
    try:
        try:
            config = _prepareconfig(args, plugins)
        except ConftestImportFailure as e:
            exc_info = ExceptionInfo.from_exc_info(e.excinfo)
            tw = TerminalWriter(sys.stderr)
            tw.line(f"ImportError while loading conftest '{e.path}'.", red=True)
            exc_info.traceback = exc_info.traceback.filter(
                filter_traceback_for_conftest_import_failure
            )
            exc_repr = (
                exc_info.getrepr(style="short", chain=False)
                if exc_info.traceback
                else exc_info.exconly()
            )
            formatted_tb = str(exc_repr)
            for line in formatted_tb.splitlines():
                tw.line(line.rstrip(), red=True)
            return ExitCode.USAGE_ERROR
        else:
            try:
                config.hook.pytest_collection_finish = pytest_collection_finish
                ret: Union[ExitCode, int] = config.hook.pytest_cmdline_main(
                    config=config
                )
                try:
                    return ExitCode(ret)
                except ValueError:
                    return ret
            finally:
                config._ensure_unconfigure()
    except UsageError as e:
        tw = TerminalWriter(sys.stderr)
        for msg in e.args:
            tw.line(f"ERROR: {msg}\n", red=True)
        return ExitCode.USAGE_ERROR


if __name__ == "__main__":
    main(sys.argv[1:])
