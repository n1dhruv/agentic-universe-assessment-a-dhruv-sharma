"""Append-only encrypted events and derived linking/classification.

Quarantine is derived, not a destructive move: new leads or call events can
resolve earlier orphans without changing any original ledger entry.
"""

from collections import defaultdict
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import re

from .leads import SCHEMAS
from .normalize import phone


IST = timezone(timedelta(hours=5, minutes=30))
COUNTERS = ('events_total', 'malformed_events', 'duplicate_events_dropped')
EVENT_TYPES = {'call.initiated', 'call.connected', 'call.ended', 'call.telephony_failed',
               'disposition.set', 'disposition.override'}


def timestamp(value):
    """Normalize supported event times to UTC; an absent offset means IST."""
    if not isinstance(value, str) or not re.fullmatch(
        r'[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2}'
        r'(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})?', value
    ):
        raise ValueError('Unsupported event timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=IST)
    return parsed.astimezone(timezone.utc)


def reject_constant(_):
    # Python otherwise accepts NaN/Infinity, which are not valid JSON numbers.
    raise ValueError('Invalid JSON constant')


def import_events(connection, privacy, text):
    stats = dict.fromkeys(COUNTERS, 0)
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        stats['events_total'] += 1
        try:
            event = json.loads(line, parse_constant=reject_constant)
        except ValueError:
            event = None
        if not isinstance(event, dict) or not isinstance(event.get('event_id'), str) or not event['event_id']:
            stats['malformed_events'] += 1
            continue
        if connection.execute('SELECT 1 FROM events WHERE event_id=?', (event['event_id'],)).fetchone():
            stats['duplicate_events_dropped'] += 1
            continue
        try:
            if not isinstance(event.get('event_type'), str) or event['event_type'] not in EVENT_TYPES:
                raise ValueError()
            if not all(isinstance(event.get(name), str) and event[name] for name in ('workflow_id', 'call_id')):
                raise ValueError()
            if not isinstance(event.get('payload', {}), dict):
                raise ValueError()
            timestamp(event.get('occurred_at'))
        except (ValueError, OverflowError):
            raise ValueError(f'Unsupported event structure at line {line_number}; drop rolled back') from None
        connection.execute('INSERT INTO events VALUES (?,?)', (event['event_id'], privacy.encrypt(event)))
    return stats


def load_catalogue():
    with (SCHEMAS/'dispositions.csv').open(newline='', encoding='utf-8') as stream:
        return {(row['workflow_id'], row['code']): {
            'is_terminal': row['is_terminal'] == 'true',
            'is_success': row['is_success'] == 'true',
        } for row in csv.DictReader(stream)}


@dataclass(frozen=True)
class LinkedEvent:
    event_id: str
    workflow_id: str
    call_id: str
    event_type: str
    occurred_at: datetime
    lead_id: int
    payload: dict


@dataclass
class Resolution:
    eligible: list[LinkedEvent]
    quarantined: dict[str, str]

    @property
    def counts(self):
        return {
            'eligible_events': len(self.eligible),
            'orphan_events': sum(reason == 'orphan' for reason in self.quarantined.values()),
            'unknown_disposition_events': sum(reason == 'unknown_disposition' for reason in self.quarantined.values()),
        }


def resolve_events(connection, privacy):
    """Rebuild links against all current leads; never modify stored events.

Only an unambiguous workflow/call ownership can link a phone-free override.
An ordinary event must match its own phone; a shared call ID is not a fallback.
"""
    leads = {(row['workflow_id'], row['phone_token']): row['id']
             for row in connection.execute('SELECT id,workflow_id,phone_token FROM leads')}
    events = [privacy.decrypt(row[0]) for row in
              connection.execute('SELECT body_encrypted FROM events ORDER BY event_id')]
    direct_links, call_owners = {}, defaultdict(set)
    for event in events:
        if event['event_type'] == 'disposition.override':
            continue
        try:
            canonical = phone(event.get('phone', ''))
        except (ValueError, TypeError):
            continue
        lead_id = leads.get((event['workflow_id'], privacy.phone_token(canonical)))
        if lead_id is not None:
            direct_links[event['event_id']] = lead_id
            call_owners[event['workflow_id'], event['call_id']].add(lead_id)
    catalogue = load_catalogue()
    result = Resolution([], {})
    for event in events:
        lead_id = direct_links.get(event['event_id'])
        if event['event_type'] == 'disposition.override':
            owners = call_owners[event['workflow_id'], event['call_id']]
            if len(owners) == 1:
                lead_id = next(iter(owners))
        if lead_id is None:
            result.quarantined[event['event_id']] = 'orphan'
            continue
        if event['event_type'].startswith('disposition.'):
            code = event.get('payload', {}).get('disposition_code')
            if not isinstance(code, str) or (event['workflow_id'], code) not in catalogue:
                result.quarantined[event['event_id']] = 'unknown_disposition'
                continue
        result.eligible.append(LinkedEvent(
            event['event_id'], event['workflow_id'], event['call_id'], event['event_type'],
            timestamp(event['occurred_at']), lead_id, event.get('payload', {}),
        ))
    return result


def quality_summary(connection, privacy, resolution=None):
    """Return persisted import totals and current event classifications, without PII."""
    names = ('lead_rows_total', 'lead_rows_rejected', 'duplicate_lead_rows_merged',
             'field_warnings', *COUNTERS)
    result = dict.fromkeys(names, 0)
    for row in connection.execute('SELECT stats FROM sources'):
        stats = json.loads(row[0])
        for name in names:
            result[name] += stats.get(name, 0)
    result['rejections_by_reason'] = {row[0]: row[1] for row in connection.execute(
        'SELECT reason,count(*) FROM rejections GROUP BY reason ORDER BY reason')}
    counts = (resolution if resolution is not None else resolve_events(connection, privacy)).counts
    result['orphan_events'] = counts['orphan_events']
    result['unknown_disposition_events'] = counts['unknown_disposition_events']
    return result
