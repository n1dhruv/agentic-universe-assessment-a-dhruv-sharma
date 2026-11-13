# Inspect the SQLite Database

SQLite stores the database in a local file, not a running server. Use read-only mode while exploring it.

## Open the Phase 3 database

```bash
cd /home/dhruv/assessment-a
sqlite3 -readonly var/my-phase3.sqlite3
```

This is the populated database created while following the Phase 3 commands. The separate default `var/assessment.sqlite3` may still be empty. If a filename is missing, read-only mode fails rather than silently creating an empty database.

Inside SQLite, enter:

```sql
.headers on
.mode column
.tables
.schema leads
SELECT workflow_id, COUNT(*) AS customers FROM leads GROUP BY workflow_id;
SELECT reason, COUNT(*) AS rejected_rows FROM rejections GROUP BY reason;
SELECT workflow_id, batch_id, row_number, reason FROM rejections LIMIT 10;
SELECT path, stats FROM sources ORDER BY path;
.quit
```

With the original seed-42 inputs, the Phase 3 database contains 951 motor-renewal customers, 941 feedback customers, and 108 rejected rows. It has no events until you explicitly perform a full import on that database.

## View storage without unlocking private customer values

```sql
SELECT id, workflow_id, batch_id, substr(values_encrypted, 1, 30) AS encrypted_preview
FROM leads LIMIT 5;
```

The preview is unreadable encrypted text. Names and phones are intentionally not plain database columns. The program uses the separate key file when it needs to decrypt them. Do not paste key contents into logs or documentation.

## Inspect the verified Phase 4 example

The agent's full-import example uses a separate database:

```bash
sqlite3 -readonly var/phase4-demo.sqlite3
```

Inside SQLite:

```sql
.headers on
.mode column
SELECT COUNT(*) AS customers FROM leads;
SELECT COUNT(*) AS unique_stored_events FROM events;
SELECT COUNT(*) AS rejected_rows FROM rejections;
SELECT COUNT(*) AS imported_files FROM sources;
SELECT event_id, substr(body_encrypted, 1, 30) AS encrypted_preview FROM events LIMIT 5;
SELECT path, stats FROM sources WHERE path LIKE 'events/%' ORDER BY path;
.quit
```

Expected counts after both seed-42 drops: 1892 customers, 8500 unique stored events, 108 rejections, and 8 imported files. An event is one diary entry; it is not necessarily one whole call.

## See current event matching and quality counts

The `events` table preserves original encrypted entries. Links and quarantine classifications are recalculated from the current database, so a later customer upload can resolve an earlier orphan without rewriting history.

This command prints counts only:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from solution.events import quality_summary, resolve_events
from solution.storage import open_database

connection, privacy = open_database(
    Path('var/phase4-demo.sqlite3'), Path('var/phase4-demo.keys.json'))
try:
    print(json.dumps(resolve_events(connection, privacy).counts, indent=2))
    print(json.dumps(quality_summary(connection, privacy), indent=2))
finally:
    connection.close()
PY
```

Expected event classification: 8020 eligible events, 462 orphan events, and 18 unknown-disposition events. Their sum is 8500 stored events. This query does not generate the Phase 5 reports.

## Reports available after Phase 5

To turn the inspected database into the five human-readable reports:

```bash
.venv/bin/python -m solution report --out reports/phase5-demo --db var/phase4-demo.sqlite3 --key-file var/phase4-demo.keys.json
```

The report command reads stored data without changing it. See [Phase 5](phase-05-reports.md) for output meanings and expected counts.
