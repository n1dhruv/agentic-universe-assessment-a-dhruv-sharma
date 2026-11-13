"""Schema-driven CSV ingestion. Call events are deliberately outside Phase 3."""

import csv
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
    """Preserve the lead-only entry point while shared ingestion owns transactions."""
    from .ingest import import_drop as import_shared_drop
    return import_shared_drop(connection, privacy, drop, schemas)


def ingest_leads(connection, privacy, path):
    """Import customers only; preserve the Phase 3 API and counter format."""
    from .ingest import ingest
    return ingest(connection, privacy, path, leads_only=True)
