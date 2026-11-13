"""Schema-driven CSV ingestion. Call events are deliberately outside Phase 3."""

import csv
import hashlib
import io
import json
from pathlib import Path

from .normalize import header, normalize_row


SCHEMAS = Path(__file__).resolve().parent.parent / 'assignment-a-data' / 'schemas'
COUNTERS = ('lead_rows_total', 'lead_rows_rejected', 'duplicate_lead_rows_merged', 'field_warnings')


def load_schemas():
    schemas = {}
    for path in sorted(SCHEMAS.glob('*.json')):
        value = json.loads(path.read_text(encoding='utf-8'))
        schemas[value['workflow_id']] = value
    if not schemas:
        raise ValueError('Workflow schemas are missing')
    return schemas


def import_file(connection, privacy, path, source, text, fields):
    workflow, batch = path.parent.name, path.stem
    stats = dict.fromkeys(COUNTERS, 0)
    aliases = {header(alias): field['name'] for field in fields
               for alias in [field['name'], *field.get('aliases', [])]}
    reader = csv.reader(io.StringIO(text), strict=True)
    columns = next(reader, [])
    mapped = [aliases.get(header(column)) for column in columns]
    recognized = [name for name in mapped if name is not None]
    if len(recognized) != len(set(recognized)):
        raise ValueError('Multiple headers map to the same schema field')
    row_number = 0
    for cells in reader:
        if not any(value.strip() for value in cells):
            continue
        if len(cells) > len(columns):
            raise ValueError('CSV row has more values than headers')
        row_number += 1
        stats['lead_rows_total'] += 1
        raw = {name: value for name, value in zip(mapped, cells) if name is not None}
        values, reason, warnings = normalize_row(fields, raw)
        if reason:
            stats['lead_rows_rejected'] += 1
            connection.execute('INSERT INTO rejections VALUES (?,?,?,?,?)',
                               (source, workflow, batch, row_number, reason))
            continue
        stats['field_warnings'] += warnings
        token = privacy.phone_token(values['phone'])
        existing = connection.execute('SELECT id, values_encrypted FROM leads WHERE workflow_id=? AND phone_token=?',
                                      (workflow, token)).fetchone()
        if existing:
            stats['duplicate_lead_rows_merged'] += 1
            merged = privacy.decrypt(existing['values_encrypted'])
            merged.update({key: value for key, value in values.items() if value is not None})
            connection.execute('UPDATE leads SET values_encrypted=? WHERE id=?',
                               (privacy.encrypt(merged), existing['id']))
        else:
            connection.execute('INSERT INTO leads(workflow_id,phone_token,batch_id,values_encrypted) VALUES (?,?,?,?)',
                               (workflow, token, batch, privacy.encrypt(values)))
    return stats


def import_drop(connection, privacy, drop, schemas):
    # Only lead files are registered. Phase 4 can import events from the same drop later.
    files = sorted((drop/'leads').glob('*/*.csv'), key=lambda path: (path.name, path.parent.name))
    result = {'imported_files': 0, 'skipped_files': 0, **dict.fromkeys(COUNTERS, 0)}
    with connection:
        connection.execute('BEGIN IMMEDIATE')
        for path in files:
            workflow = path.parent.name
            if workflow not in schemas:
                raise ValueError('Unknown lead workflow directory')
            source = path.relative_to(drop).as_posix()
            body = path.read_bytes()
            digest = hashlib.sha256(body).hexdigest()
            existing = connection.execute('SELECT digest FROM sources WHERE path=?', (source,)).fetchone()
            if existing:
                if existing['digest'] != digest:
                    raise ValueError('Previously imported lead file changed; use a fresh database for corrected input')
                result['skipped_files'] += 1
                continue
            connection.execute('INSERT INTO sources VALUES (?,?,?)', (source, digest, '{}'))
            try:
                stats = import_file(connection, privacy, path, source, body.decode('utf-8-sig'),
                                    schemas[workflow]['fields'])
            except (UnicodeError, csv.Error):
                raise ValueError('Invalid UTF-8 or CSV structure; drop rolled back') from None
            connection.execute('UPDATE sources SET stats=? WHERE path=?', (json.dumps(stats), source))
            result['imported_files'] += 1
            for name in COUNTERS:
                result[name] += stats[name]
    return result


def ingest_leads(connection, privacy, path):
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
    result = {'scope': 'leads_only', 'imported_files': 0, 'skipped_files': 0, **dict.fromkeys(COUNTERS, 0)}
    for drop in drops:
        for name, count in import_drop(connection, privacy, drop, schemas).items():
            result[name] += count
    return result
