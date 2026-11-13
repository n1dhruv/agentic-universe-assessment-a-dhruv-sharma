"""Command-line entry point. Run from the project root."""

import argparse
from pathlib import Path
import sqlite3


def main():
    parser = argparse.ArgumentParser(description="Import customer/call files and write reports.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("init", "Create local keys and database; preserve existing data."),
        ("ingest", "Import one drop or a directory of drops in order."),
        ("report", "Write the five required report files."),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--db", type=Path, default=Path("var/assessment.sqlite3"))
        command.add_argument("--key-file", type=Path, default=Path("var/keys.json"))
        if name == "ingest":
            command.add_argument("path", type=Path)
        if name == "report":
            command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command != "init":
            raise ValueError(f"{args.command} is not implemented yet; only Phases 1 and 2 are complete")
        from .storage import initialize
        initialize(args.db, args.key_file)
        print("Database and keys ready; existing data preserved.")
    except (ValueError, OSError, sqlite3.Error) as error:
        # Application errors contain locations and reasons, never raw customer values.
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
