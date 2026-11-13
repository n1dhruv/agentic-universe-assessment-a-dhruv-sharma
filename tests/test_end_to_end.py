"""Phase 6 process-level proof on fresh generated datasets.

Generated seeds establish repeatability and invariants. The independent exact
report answers remain the hand-calculated fixtures in test_reports.py.
"""

import csv
from datetime import datetime, timedelta
import io
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from time import perf_counter

import pytest

from solution.events import resolve_events
from solution.leads import load_schemas
from solution.storage import open_database


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ('batch_summary.csv', 'daily_overview.csv', 'lead_report.csv', 'rejections.csv', 'data_quality.json')
CSV_HEADERS = {
    'batch_summary.csv': 'workflow_id,batch_id,total_leads,yet_to_reach_out,in_progress_telephony_failed,in_progress_dialed,completed',
    'daily_overview.csv': 'workflow_id,date,total_calls,connected_calls,connectivity_rate,success_leads',
    'lead_report.csv': 'workflow_id,external_ref,batch_id,phone_masked,bucket,total_calls,connected_calls,last_call_at,current_disposition,ever_success',
    'rejections.csv': 'workflow_id,batch_id,row_number,reason',
}


def process(*args, expected_failure=False):
    result = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT,
                            capture_output=True, text=True, timeout=60)
    if expected_failure:
        assert result.returncode == 1 and 'drop rolled back' in result.stderr
        assert 'Traceback' not in result.stderr
    else:
        assert result.returncode == 0, result.stderr
    return result


def pipeline(command, db, keys, *args, **kwargs):
    return process('-m', 'solution', command, *args, '--db', db, '--key-file', keys, **kwargs)


def state(db, keys):
    """Capture logical state and classifications without logging decrypted values."""
    connection, privacy = open_database(db, keys)
    try:
        resolution = resolve_events(connection, privacy)
        return {
            'dump': list(connection.iterdump()),
            'event_bodies': dict(connection.execute('SELECT event_id,body_encrypted FROM events')),
            'orphan_ids': {key for key, reason in resolution.quarantined.items() if reason == 'orphan'},
        }
    finally:
        connection.close()


def report_files(db, keys, out):
    # Each CLI call opens the database in a new process, including repeat reports.
    pipeline('report', db, keys, '--out', out)
    assert sorted(path.name for path in out.iterdir()) == sorted(OUTPUTS)
    return {name: (out/name).read_bytes() for name in OUTPUTS}


def source_counts(data):
    leads = 0
    for path in data.glob('drop_*/leads/*/*.csv'):
        with path.open(newline='', encoding='utf-8') as stream:
            rows = csv.reader(stream)
            next(rows)
            leads += sum(any(cell.strip() for cell in row) for row in rows)
    lines = sum(sum(bool(line.strip()) for line in path.read_text().splitlines())
                for path in data.glob('drop_*/events/*.jsonl'))
    return leads, lines


def check_report_invariants(files, lead_input_count, event_input_count):
    rows = {}
    for name, header in CSV_HEADERS.items():
        content = files[name].decode('utf-8')
        assert content.splitlines()[0] == header
        rows[name] = list(csv.DictReader(io.StringIO(content)))
        assert all(None not in row for row in rows[name])
    batches, daily, leads, rejections = (rows[name] for name in CSV_HEADERS)
    quality = json.loads(files['data_quality.json'])
    assert quality['lead_rows_total'] == lead_input_count
    assert quality['events_total'] == event_input_count
    assert quality['lead_rows_total'] == len(leads) + len(rejections) + quality['duplicate_lead_rows_merged']
    assert quality['lead_rows_rejected'] == len(rejections)
    assert sum(quality['rejections_by_reason'].values()) == len(rejections)
    expected_reasons = {}
    for row in rejections:
        expected_reasons[row['reason']] = expected_reasons.get(row['reason'], 0) + 1
    assert quality['rejections_by_reason'] == expected_reasons
    assert [(row['workflow_id'], row['batch_id']) for row in batches] == sorted(
        (row['workflow_id'], row['batch_id']) for row in batches)
    assert [(row['workflow_id'], row['date']) for row in daily] == sorted(
        (row['workflow_id'], row['date']) for row in daily)
    assert [(row['workflow_id'], row['external_ref']) for row in leads] == sorted(
        (row['workflow_id'], row['external_ref']) for row in leads)
    assert [(row['workflow_id'], row['batch_id'], int(row['row_number'])) for row in rejections] == sorted(
        (row['workflow_id'], row['batch_id'], int(row['row_number'])) for row in rejections)
    buckets = ('yet_to_reach_out', 'in_progress_telephony_failed', 'in_progress_dialed', 'completed')
    assert sum(int(row['total_leads']) for row in batches) == len(leads)
    for row in batches:
        matching = [lead for lead in leads if (lead['workflow_id'], lead['batch_id']) ==
                    (row['workflow_id'], row['batch_id'])]
        assert int(row['total_leads']) == len(matching) == sum(int(row[bucket]) for bucket in buckets)
        for bucket in buckets:
            assert int(row[bucket]) == sum(lead['bucket'] == bucket for lead in matching)
    for workflow in {row['workflow_id'] for row in leads}:
        for count in ('total_calls', 'connected_calls'):
            assert sum(int(row[count]) for row in leads if row['workflow_id'] == workflow) == sum(
                int(row[count]) for row in daily if row['workflow_id'] == workflow)
    for row in leads:
        assert row['bucket'] in buckets and row['ever_success'] in {'true', 'false'}
        assert re.fullmatch(r'\+91\*{6}[0-9]{4}', row['phone_masked'])
        assert 0 <= int(row['connected_calls']) <= int(row['total_calls'])
        if row['last_call_at']:
            assert datetime.fromisoformat(row['last_call_at']).utcoffset() == timedelta(hours=5, minutes=30)
        else:
            assert row['total_calls'] == '0' and row['bucket'] == 'yet_to_reach_out'
    for row in daily:
        total, connected = int(row['total_calls']), int(row['connected_calls'])
        assert total > 0 and 0 <= connected <= total
        assert row['connectivity_rate'] == f'{connected/total:.4f}'
        assert re.fullmatch(r'[01]\.[0-9]{4}', row['connectivity_rate'])
        assert 0 <= int(row['success_leads']) <= total
    return quality, len(leads), sum(int(row['total_calls']) for row in daily)


def check_privacy_and_database(db, keys):
    """Inspect storage, sample schema-marked PII bytes, and return canonical state."""
    connection, privacy = open_database(db, keys)
    try:
        assert connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert list(connection.execute('PRAGMA foreign_key_check')) == []
        lead_records = list(connection.execute('SELECT * FROM leads ORDER BY id'))
        schemas = load_schemas()
        canonical = {}
        for record in lead_records:
            values = privacy.decrypt(record['values_encrypted'])
            canonical[record['workflow_id'], values['phone']] = record['batch_id'], values
        stride = max(1, len(lead_records)//32)
        sampled = lead_records[::stride]
        stored_bytes = b''.join(path.read_bytes() for path in db.parent.glob(db.name+'*') if path.is_file())
        for record in sampled:
            values = privacy.decrypt(record['values_encrypted'])
            for field in schemas[record['workflow_id']]['fields']:
                if field.get('pii') and values.get(field['name']):
                    value = values[field['name']]
                    assert value.encode() not in stored_bytes
                    if field['type'] == 'phone':
                        assert value[-10:].encode() not in stored_bytes
        for value in json.loads(keys.read_text()).values():
            assert value.encode() not in stored_bytes
        assert keys.stat().st_mode & 0o777 == 0o600
        events = {row[0]: privacy.decrypt(row[1]) for row in connection.execute('SELECT * FROM events')}
        return canonical, events, len(sampled)
    finally:
        connection.close()


@pytest.mark.parametrize('seed', [42, 7, 99])
def test_generated_pipeline_across_processes(seed, tmp_path):
    started = perf_counter()
    data = tmp_path/'data'
    process('assignment-a-data/tools/generate_data.py', '--seed', seed, '--scale', 'small', '--out', data)
    lead_input_count, event_input_count = source_counts(data)
    db, keys = tmp_path/'sequential.sqlite3', tmp_path/'sequential.keys.json'
    pipeline('init', db, keys)
    first = json.loads(pipeline('ingest', db, keys, data/'drop_1').stdout)
    partial_files = report_files(db, keys, tmp_path/'partial_reports')
    first_state = state(db, keys)
    assert json.loads(partial_files['data_quality.json']) == first['quality']
    original_keys = keys.read_bytes()
    failure_retried = False
    if seed == 42:
        # Fail after drop-2 leads and earlier events have been processed. The CLI
        # must roll back the whole drop, including source markers and merges.
        target = sorted((data/'drop_2'/'events').glob('*.jsonl'))[-1]
        original = target.read_bytes()
        target.write_bytes(original + b'\n{"event_id":"phase6-injected-failure","event_type":"call.initiated"}\n')
        try:
            pipeline('ingest', db, keys, data/'drop_2', expected_failure=True)
            assert state(db, keys)['dump'] == first_state['dump']
            assert report_files(db, keys, tmp_path/'after_failure_reports') == partial_files
        finally:
            target.write_bytes(original)
        failure_retried = True
    second = json.loads(pipeline('ingest', db, keys, data/'drop_2').stdout)
    final_state = state(db, keys)
    for event_id, encrypted in first_state['event_bodies'].items():
        assert final_state['event_bodies'][event_id] == encrypted
    resolved_earlier = len(first_state['orphan_ids'] - final_state['orphan_ids'])
    assert resolved_earlier > 0
    final_files = report_files(db, keys, tmp_path/'final_reports')
    quality, lead_count, call_count = check_report_invariants(final_files, lead_input_count, event_input_count)
    assert quality == second['quality']
    assert len(final_state['event_bodies']) == quality['events_total'] - quality['malformed_events'] - quality['duplicate_events_dropped']
    assert len(final_state['event_bodies']) == sum(second['event_state'].values())
    before = state(db, keys)['dump']
    repeated = json.loads(pipeline('ingest', db, keys, data).stdout)
    assert repeated['imported_files'] == 0 and repeated['skipped_files'] > 0
    assert all(repeated[name] == 0 for name in (
        'events_total', 'malformed_events', 'duplicate_events_dropped', 'lead_rows_total',
        'lead_rows_rejected', 'duplicate_lead_rows_merged', 'field_warnings'))
    assert repeated['quality'] == quality
    assert state(db, keys)['dump'] == before
    assert report_files(db, keys, tmp_path/'reopened_reports') == final_files
    assert state(db, keys)['dump'] == before
    assert keys.read_bytes() == original_keys
    canonical, events, privacy_samples = check_privacy_and_database(db, keys)
    combined_db, combined_keys = tmp_path/'combined.sqlite3', tmp_path/'combined.keys.json'
    pipeline('init', combined_db, combined_keys)
    pipeline('ingest', combined_db, combined_keys, data)
    assert report_files(combined_db, combined_keys, tmp_path/'combined_reports') == final_files
    combined_leads, combined_events, _ = check_privacy_and_database(combined_db, combined_keys)
    assert canonical == combined_leads and events == combined_events
    summary = {
        'seed': seed, 'leads': lead_count, 'calls': call_count,
        'stored_events': len(events), 'earlier_orphans_resolved': resolved_earlier,
        'privacy_sampled_leads_per_database': privacy_samples,
        'failure_rollback_and_retry': failure_retried,
        'repeat_unchanged': True, 'combined_reports_identical': True,
        'reopened_reports_identical': True, 'seconds': round(perf_counter()-started, 4),
    }
    print('PHASE6_RESULT ' + json.dumps(summary, sort_keys=True))
