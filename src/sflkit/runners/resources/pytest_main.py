import os
import sys
from typing import Union

# noinspection PyPackageRequirements
from _pytest.config import (
    _prepareconfig,
    ConftestImportFailure,
    UsageError,
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
    args=None,
    plugins=None,
) -> int:
    """Perform an in-process test run.

    :param args: List of command line arguments.
    :param plugins: List of plugin objects to be auto-registered during initialization.

    :returns: An exit code.
    """
    try:
        try:
            config = _prepareconfig(args, plugins)
        except ConftestImportFailure:
            return 4
        else:
            try:
                config.hook.pytest_collection_finish = pytest_collection_finish
                ret = config.hook.pytest_cmdline_main(config=config)
                return ret
            finally:
                config._ensure_unconfigure()
    except UsageError:
        return 4


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
