#!/usr/bin/env python
"""Calls include-what-you-use on a kernel .c file"""

import argparse
import json
from pathlib import Path
from typing import List

from lib.utils import warn, perform_iwyu

DEBUG = False


def main(commands: Path, fixer_path: Path, filters: List[Path], specific: str):
    """Chooses a specific file to call perform_iwyu on"""

    current_dir = Path(__file__).resolve().parent
    filters += [Path(current_dir, "filter.imp"), Path(current_dir, "symbol.imp")]

    with open(commands, encoding="utf-8") as file:
        eligible = [x for x in json.load(file) if specific in x["file"]]
        if len(eligible) == 0:
            warn("NO FILE WITH IDENTIFIER FOUND")
        for part in eligible:
            if not "arch" in part["file"]:
                perform_iwyu(
                    fixer_path,
                    part,
                    filters + [Path(current_dir), "nonarch.imp"],
                    current_dir,
                    debug=DEBUG,
                )
            else:
                perform_iwyu(fixer_path, part, filters, current_dir, debug=DEBUG)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""This script attempts to automatically refactor a
                                    include list without touching the headers themselves."""
    )

    parser.add_argument(
        "-c",
        "--commands",
        type=Path,
        required=True,
        help="Path to compile_commands.json",
    )
    parser.add_argument(
        "-f",
        "--fixer_path",
        type=Path,
        help="Path to the fix_includes.py",
        default=Path(
            Path(__file__).resolve().parent, "include-what-you-use/fix_includes.py"
        ),
    )
    parser.add_argument(
        "-s",
        "--specific_command",
        required=True,
        help="Name of the .c file to refactor",
    )
    parser.add_argument(
        "-fi", "--filters", nargs="*", help="List of additional filters", default=[]
    )
    parser.add_argument(
        "-d", action="store_true", help="Debug mode on. Prints IWYU output."
    )

    args = parser.parse_args()

    DEBUG = args.d

    main(args.commands, args.fixer_path, args.filters, args.specific_command)
