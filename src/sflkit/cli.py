import argparse
import json
import logging
from typing import Any

import sflkit
from sflkit.analysis.suggestion import Suggestion, Location

INSTRUMENT = "instrument"
ANALYZE = "analyze"


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


def main(args):
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    if args.command == INSTRUMENT:
        sflkit.instrument(args.config, args.events)
    elif args.command == ANALYZE:
        results = sflkit.analyze(args.config, args.analysis)
        with open(args.out, "w") as output:
            json.dump(results, output, cls=ResultEncoder, indent=4)


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
    arg_parser.add_argument(
        "-c", "--config", dest="config", required=True, help="path to the config file"
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
        "-e",
        "--events",
        dest="events",
        default=None,
        help="the destination of the found predicates file "
        "for the project (default: events.json)",
    )

    analyze_parser = commands.add_parser(
        ANALYZE,
        description="The analyze command analyzes the collected predicates on a "
        "subject to detect the statistically correlating ones.",
        help="execute the analysis of the collected predicates",
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
    return arg_parser.parse_args(args=args, namespace=namespace)


if __name__ == "__main__":
    main(parse_args())
