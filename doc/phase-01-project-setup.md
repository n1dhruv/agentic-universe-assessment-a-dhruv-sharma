# Phase 1: Project Setup and Command Interface

Status: Complete. Target: 30 minutes. Dependency: none.

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

- [x] Starter instructions and schemas are present and preserved.
- [x] CLI help describes each command and its options.
- [x] Sample data contains both drops and workflows.
- [x] Generated files and secrets are ignored by Git.
- [x] Setup commands are recorded for later clean-checkout verification.

At this stage, command scaffolding does not imply ingestion or reporting is complete.

## Evidence

Pending: record Python version, setup commands, CLI help check, and generator result.

## Execution evidence and self-check

Created CLI help, restored the supplied Assessment A assets through web retrieval, generated seed 42 (4247 and 4498 event lines), and verified Git ignores. Run `.venv/bin/python -m solution --help` and `.venv/bin/python assignment-a-data/tools/generate_data.py --seed 42 --scale small --out data`. Python 3.14.8 is used. Git/PyPI DNS failed; offline resolver attempts also failed. Copied installed cryptography 50.0.1, cffi 2.1.1, pytest 9.1.1 and supporting distributions into the isolated venv; crypto round-trip and pytest imports pass. Original Git history could not be fetched; existing project history is preserved. Clean internet dependency installation is not yet verified.

## Simple explanation and commands

The project now has the assignment instructions, customer-data rules, fake-data generator, its own Python environment, and terminal commands. This is the prepared workbench; complete reports are not available yet.

```bash
cd /home/dhruv/assessment-a
.venv/bin/python -m solution --help
.venv/bin/python assignment-a-data/tools/generate_data.py --seed 42 --scale small --out data
```

Expected: help lists `init`, `ingest`, and `report`. The generator creates `data/drop_1` and `data/drop_2`, reporting 4247 and 4498 event lines. The same seed regenerates the same inputs. Dependency installation from the internet remains unverified because GitHub/PyPI DNS failed; the local environment uses existing installed dependency distributions.
