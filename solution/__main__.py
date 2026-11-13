"""Command-line entry point. Run from the project root."""

import argparse
import json
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
            command.add_argument("--leads-only", action="store_true",
                                 help="Import customer CSVs only; event processing is not implemented yet.")
        if name == "report":
            command.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        from .storage import initialize, open_database
        if args.command == "init":
            initialize(args.db, args.key_file)
            print("Database and keys ready; existing data preserved.")
        elif args.command == "ingest" and args.leads_only:
            from .leads import ingest_leads
            connection, privacy = open_database(args.db, args.key_file)
            try:
                result = ingest_leads(connection, privacy, args.path)
                print(json.dumps(result, sort_keys=True))
            finally:
                connection.close()
        elif args.command == "ingest":
            raise ValueError("Call-event ingestion is not implemented yet; use --leads-only for Phase 3")
        else:
            raise ValueError("report is not implemented yet; it belongs to Phase 5")
    except (ValueError, OSError, sqlite3.Error) as error:
        # Application errors contain locations and reasons, never raw customer values.
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
