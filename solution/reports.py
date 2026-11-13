"""Derive shared call facts and render the five contracted report files."""

from collections import defaultdict
import csv
from dataclasses import dataclass
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from .events import IST, LinkedEvent, load_catalogue, quality_summary, resolve_events
from .leads import load_schemas
from .normalize import apply_defaults


BUCKETS = ('yet_to_reach_out', 'in_progress_telephony_failed', 'in_progress_dialed', 'completed')
HEADERS = {
    'batch_summary.csv': ['workflow_id', 'batch_id', 'total_leads', *BUCKETS],
    'daily_overview.csv': ['workflow_id', 'date', 'total_calls', 'connected_calls', 'connectivity_rate', 'success_leads'],
    'lead_report.csv': ['workflow_id', 'external_ref', 'batch_id', 'phone_masked', 'bucket',
                        'total_calls', 'connected_calls', 'last_call_at', 'current_disposition', 'ever_success'],
    'rejections.csv': ['workflow_id', 'batch_id', 'row_number', 'reason'],
}


@dataclass(frozen=True)
class CallFacts:
    workflow_id: str
    call_id: str
    lead_id: int
    initiation: LinkedEvent
    connected: bool
    telephony_failed: bool
    disposition: str
    terminal: bool
    success: bool

    @property
    def order_key(self):
        return self.initiation.occurred_at, self.initiation.event_id, self.call_id


def event_order(event):
    return event.occurred_at, event.event_id


def build_call_facts(eligible, catalogue):
    """Only initiated, linked calls contribute to business reports."""
    grouped = defaultdict(list)
    for event in eligible:
        grouped[event.workflow_id, event.call_id, event.lead_id].append(event)
    calls = []
    for (workflow, call_id, lead_id), events in sorted(grouped.items()):
        starts = [event for event in events if event.event_type == 'call.initiated']
        if not starts:
            continue
        # The supplied data has one initiation per call. If multiple distinct
        # initiation events exist, use the earliest instant as the call start.
        initiation = min(starts, key=event_order)
        overrides = [event for event in events if event.event_type == 'disposition.override']
        ordinary = [event for event in events if event.event_type == 'disposition.set']
        candidates = overrides or ordinary
        disposition = max(candidates, key=event_order).payload['disposition_code'] if candidates else ''
        outcome = catalogue.get((workflow, disposition), {})
        calls.append(CallFacts(
            workflow, call_id, lead_id, initiation,
            any(event.event_type == 'call.connected' for event in events),
            any(event.event_type == 'call.telephony_failed' for event in events),
            disposition, outcome.get('is_terminal', False), outcome.get('is_success', False),
        ))
    return calls


def lead_bucket(calls):
    if not calls:
        return 'yet_to_reach_out'
    if any(call.terminal for call in calls):
        return 'completed'
    if all(call.telephony_failed for call in calls):
        return 'in_progress_telephony_failed'
    return 'in_progress_dialed'


def csv_text(name, rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=HEADERS[name], lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def render_reports(connection, privacy):
    """Calculate all outputs from a consistent read snapshot; write no database rows."""
    if connection.in_transaction:
        raise ValueError('Finish the current transaction before generating reports')
    with connection:
        connection.execute('BEGIN')
        schemas, catalogue = load_schemas(), load_catalogue()
        resolution = resolve_events(connection, privacy)
        calls = build_call_facts(resolution.eligible, catalogue)
        by_lead, by_day, batches = defaultdict(list), defaultdict(list), {}
        for call in calls:
            by_lead[call.lead_id].append(call)
            day = call.initiation.occurred_at.astimezone(IST).date().isoformat()
            by_day[call.workflow_id, day].append(call)
        leads = []
        for record in connection.execute('SELECT * FROM leads ORDER BY id'):
            workflow, batch = record['workflow_id'], record['batch_id']
            fields = schemas[workflow]['fields']
            values = apply_defaults(fields, privacy.decrypt(record['values_encrypted']))
            reference = next(field['name'] for field in fields if field.get('reference'))
            customer_calls = sorted(by_lead[record['id']], key=lambda call: call.order_key)
            bucket = lead_bucket(customer_calls)
            summary = batches.setdefault((workflow, batch), {
                'workflow_id': workflow, 'batch_id': batch, 'total_leads': 0,
                **dict.fromkeys(BUCKETS, 0),
            })
            summary['total_leads'] += 1
            summary[bucket] += 1
            outcomes = [call for call in customer_calls if call.disposition]
            row = {
                'workflow_id': workflow, 'external_ref': values[reference], 'batch_id': batch,
                'phone_masked': '+91******' + values['phone'][-4:], 'bucket': bucket,
                'total_calls': len(customer_calls), 'connected_calls': sum(call.connected for call in customer_calls),
                'last_call_at': customer_calls[-1].initiation.occurred_at.astimezone(IST).isoformat() if customer_calls else '',
                'current_disposition': outcomes[-1].disposition if outcomes else '',
                'ever_success': str(any(call.success for call in customer_calls)).lower(),
            }
            # Canonical phone resolves otherwise unspecified reference ties without
            # depending on insertion order or the database's secret HMAC key.
            leads.append(((workflow, values[reference], values['phone']), row))
        daily = []
        for (workflow, day), daily_calls in sorted(by_day.items()):
            connected = sum(call.connected for call in daily_calls)
            daily.append({
                'workflow_id': workflow, 'date': day, 'total_calls': len(daily_calls),
                'connected_calls': connected, 'connectivity_rate': f'{connected / len(daily_calls):.4f}',
                'success_leads': len({call.lead_id for call in daily_calls if call.success}),
            })
        rejections = [dict(row) for row in connection.execute(
            'SELECT workflow_id,batch_id,row_number,reason FROM rejections '
            'ORDER BY workflow_id,batch_id,row_number,source_path')]
        outputs = {
            'batch_summary.csv': csv_text('batch_summary.csv', [batches[key] for key in sorted(batches)]),
            'daily_overview.csv': csv_text('daily_overview.csv', daily),
            'lead_report.csv': csv_text('lead_report.csv', [row for _, row in sorted(leads, key=lambda item: item[0])]),
            'rejections.csv': csv_text('rejections.csv', rejections),
            'data_quality.json': json.dumps(quality_summary(connection, privacy, resolution), indent=2, sort_keys=True) + '\n',
        }
    return outputs


def write_reports(connection, privacy, out, *, protected_paths=()):
    """Stage every file first, then replace each destination atomically.

    Individual files cannot be half-written. The five-file directory is not an
    atomic unit: a filesystem failure during replacement can leave mixed versions.
    """
    out = Path(out)
    protected = {Path(path).resolve() for path in protected_paths}
    protected.update(Path(row[2]).resolve() for row in connection.execute('PRAGMA database_list') if row[2])
    outputs = render_reports(connection, privacy)
    for name in outputs:
        destination = out/name
        if destination.resolve() in protected or destination.is_dir():
            raise ValueError('Report destination conflicts with a protected file or directory')
    out.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.report-', dir=out) as temporary:
        staged = Path(temporary)
        for name, content in outputs.items():
            (staged/name).write_text(content, encoding='utf-8', newline='')
        for name in outputs:
            (staged/name).replace(out/name)
