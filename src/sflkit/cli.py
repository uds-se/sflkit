import argparse
import json
import logging
import os
import sys
from typing import Any

import sflkit
from sflkit.analysis.suggestion import Suggestion, Location
from sflkit.config import hash_identifier
from sflkit.logger import LOGGER
from sflkit.mapping import EventMapping
from sflkit.model import EventFile

INSTRUMENT = "instrument"
RUN = "run"
ANALYZE = "analyze"
READ = "read"


class ResultEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Suggestion):
            return {
                "locations": [self.default(line) for line in o.lines],
                "suspiciousness": o.suspiciousness,
            }
        elif isinstance(o, Location):
            return f"{o.file}:{o.line}"
        else:
            return super().default(o)


def main(*args: str, stdout=sys.stdout, stderr=sys.stderr):
    if "-O" in sys.argv:
        sys.argv.remove("-O")
        os.execl(sys.executable, sys.executable, "-O", *sys.argv)

    if stdout is not None:
        sys.stdout = stdout
    if stderr is not None:
        sys.stderr = stderr

    args = parse_args(args or sys.argv[1:])

    if args.debug:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)
    if args.command == INSTRUMENT:
        sflkit.instrument(args.config)
    elif args.command == RUN:
        sflkit.run(args.config, args.out)
    elif args.command == ANALYZE:
        results = sflkit.analyze(args.config, args.analysis)
        with open(args.out, "w") as output:
            json.dump(results, output, cls=ResultEncoder, indent=4)
    elif args.command == READ:
        mapping = EventMapping.load_from_file(hash_identifier(args.target))
        with EventFile(args.event_file, 0, mapping) as event_file:
            for i, event in enumerate(event_file.load()):
                print(f"{i:>5}: {event}")
                if (i + 1) % 10 == 0:
                    input("Press Enter to continue... ")
                    print("\033[F\033[K", end="")


def parse_args(args=None, namespace=None):
    arg_parser = argparse.ArgumentParser(
        prog="SFLKit",
        description="A workbench for statistical fault localization python programs"
        "and in the future other programs.",
    )
    arg_parser.add_argument(
        "--debug",
        action="store_true",
        dest="debug",
        default=False,
        help="the debug flag to activate debug information",
    )
    commands = arg_parser.add_subparsers(
        title="command",
        description="The framework allows for the execution of various commands.",
        help="the command to execute",
        dest="command",
        required=True,
    )

    instrument_parser = commands.add_parser(
        INSTRUMENT,
        description="The instrumentation command instruments a subject to collect "
        "various predicates during its execution.",
        help="execute the instrumentation of subject",
    )
    instrument_parser.add_argument(
        "-c", "--config", dest="config", required=True, help="path to the config file"
    )

    analyze_parser = commands.add_parser(
        ANALYZE,
        description="The analyze command analyzes the collected predicates on a "
        "subject to detect the statistically correlating ones.",
        help="execute the analysis of the collected predicates",
    )
    analyze_parser.add_argument(
        "-c", "--config", dest="config", required=True, help="path to the config file"
    )
    analyze_parser.add_argument(
        "-a",
        "--analysis",
        dest="analysis",
        default=None,
        help="The dump file of the counts of the relevant and irrelevant, "
        "true and false analysis objects",
    )
    analyze_parser.add_argument(
        "-o",
        "--out",
        dest="out",
        default="out.json",
        help="The report of the final results, i.e. the suggestions sorted by analysis",
    )

    run_parser = commands.add_parser(
        RUN,
        description="The run command executes the tests of the subject and creates the event files.",
        help="execute the tests and collect predicates",
    )
    run_parser.add_argument(
        "-c", "--config", dest="config", required=True, help="path to the config file"
    )
    run_parser.add_argument(
        "-o",
        "--out",
        dest="out",
        default=None,
        help="The output path of the event files.",
    )

    read_parser = commands.add_parser(
        READ,
        description="The read command reads an event file and prints the events.",
        help="read an event file",
    )
    read_parser.add_argument(
        "-e",
        "--events",
        dest="event_file",
        required=True,
        help="The input path of the event file.",
    )
    read_parser.add_argument(
        "-t",
        "--target",
        dest="target",
        required=True,
        help="The path of the target to investigate.",
    )

    return arg_parser.parse_args(args=args, namespace=namespace)


if __name__ == "__main__":
    if "-O" in sys.argv:
        sys.argv.remove("-O")
        os.execl(sys.executable, sys.executable, "-O", *sys.argv)
    else:
        main()
