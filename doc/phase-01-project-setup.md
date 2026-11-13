# Phase 1: Project Setup and Command Interface

Status: Not started. Target: 30 minutes. Dependency: none.

## Outcome

A runnable project with starter materials, sample input, and a stable command interface.

## Work

1. Bring the starter repository into the existing project directory without overwriting `AGENTS.md` or `doc/`. Preserve starter structure and history where available.
2. Read the assessment README, glossary, schemas, disposition catalogue, and submission templates.
3. Create a Python 3.11+ virtual environment. Retain starter dependencies; add `cryptography` and use `pytest`.
4. Create the `solution/` package and `tests/`. Expose `init`, `ingest`, and `report` through `python -m solution`.
5. Default local storage to `var/assessment.sqlite3` and keys to `var/keys.json`. Ignore `var/`, generated datasets, reports, virtual environments, and `.env` files.
6. Reserve optional `--db` and `--key-file` arguments on pipeline commands. Use nonzero exits and clear messages for invalid command usage.
7. Generate sample data with the unmodified supplied generator:

```bash
python assignment-a-data/tools/generate_data.py --seed 42 --scale small --out data
```

## Completion checks

- [ ] Starter instructions and schemas are present and preserved.
- [ ] CLI help describes each command and its options.
- [ ] Sample data contains both drops and workflows.
- [ ] Generated files and secrets are ignored by Git.
- [ ] Setup commands are recorded for later clean-checkout verification.

At this stage, command scaffolding does not imply ingestion or reporting is complete.

## Evidence

Pending: record Python version, setup commands, CLI help check, and generator result.
