"""Drop discovery, source identity, and transaction ownership for ingestion."""

import csv
import hashlib
import json
from pathlib import Path

from .leads import COUNTERS as LEAD_COUNTERS, import_file, load_schemas


def import_drop(connection, privacy, drop, schemas, *, leads_only=True):
    # Lead-only mode registers no event files, allowing a later full import of the same drop.
    files = sorted((drop/'leads').glob('*/*.csv'), key=lambda path: (path.name, path.parent.name))
    counters = LEAD_COUNTERS
    if not leads_only:
        from .events import COUNTERS as EVENT_COUNTERS, import_events
        files.extend(sorted((drop/'events').glob('*.jsonl')))
        counters = (*LEAD_COUNTERS, *EVENT_COUNTERS)
    result = {'imported_files': 0, 'skipped_files': 0, **dict.fromkeys(counters, 0)}
    with connection:
        connection.execute('BEGIN IMMEDIATE')
        for path in files:
            if path.suffix == '.csv' and path.parent.name not in schemas:
                raise ValueError('Unknown lead workflow directory')
            source = path.relative_to(drop).as_posix()
            body = path.read_bytes()
            digest = hashlib.sha256(body).hexdigest()
            existing = connection.execute('SELECT digest FROM sources WHERE path=?', (source,)).fetchone()
            if existing:
                if existing['digest'] != digest:
                    kind = 'lead file' if path.suffix == '.csv' else 'event file'
                    raise ValueError(f'Previously imported {kind} changed; use a fresh database for corrected input')
                result['skipped_files'] += 1
                continue
            connection.execute('INSERT INTO sources VALUES (?,?,?)', (source, digest, '{}'))
            try:
                text = body.decode('utf-8-sig')
                if path.suffix == '.csv':
                    stats = import_file(connection, privacy, path, source, text,
                                        schemas[path.parent.name]['fields'])
                else:
                    stats = import_events(connection, privacy, text)
            except (UnicodeError, csv.Error):
                raise ValueError('Invalid UTF-8 or CSV structure; drop rolled back') from None
            connection.execute('UPDATE sources SET stats=? WHERE path=?', (json.dumps(stats), source))
            result['imported_files'] += 1
            for name in counters:
                result[name] += stats.get(name, 0)
    return result


def ingest(connection, privacy, path, *, leads_only=False):
    """Import a single drop or sorted child drops; return counts for new files only."""
    path = Path(path)
    if not path.is_dir():
        raise ValueError('Input directory does not exist')
    if (path/'leads').is_dir() or (path/'events').is_dir():
        drops = [path]
    else:
        drops = [item for item in sorted(path.iterdir()) if item.is_dir() and
                 ((item/'leads').is_dir() or (item/'events').is_dir())]
    if not drops:
        raise ValueError('No drops found; expected a leads/ directory inside each drop')
    schemas = load_schemas()
    counters = LEAD_COUNTERS
    if not leads_only:
        from .events import COUNTERS as EVENT_COUNTERS, resolve_events, quality_summary
        counters = (*LEAD_COUNTERS, *EVENT_COUNTERS)
    result = {'scope': 'leads_only' if leads_only else 'leads_and_events',
              'imported_files': 0, 'skipped_files': 0, **dict.fromkeys(counters, 0)}
    for drop in drops:
        for name, count in import_drop(connection, privacy, drop, schemas, leads_only=leads_only).items():
            result[name] += count
    if not leads_only:
        resolution = resolve_events(connection, privacy)
        result['event_state'] = resolution.counts
        result['quality'] = quality_summary(connection, privacy, resolution)
    return result
