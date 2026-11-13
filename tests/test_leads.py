"""Customer-only import tests, retained as regression coverage for full ingestion."""

import csv
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from solution.leads import ingest_leads, load_schemas
from solution.normalize import apply_defaults
from solution.storage import initialize, open_database


HEADERS = ['customer_name', 'phone', 'policy_number', 'policy_expiry', 'premium_amount', 'preferred_language']


def write_leads(drop, rows, workflow='motor_renewal', batch='batch_001', headers=None):
    path = drop/'leads'/workflow/(batch + '.csv')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(HEADERS if headers is None else headers)
        writer.writerows(rows)
    return path


@pytest.fixture
def store(tmp_path):
    db, keys = tmp_path/'db.sqlite3', tmp_path/'keys.json'
    initialize(db, keys)
    connection, privacy = open_database(db, keys)
    yield connection, privacy
    connection.close()


def test_schema_aliases_rejections_and_counts(store, tmp_path):
    connection, privacy = store
    drop = tmp_path/'drop'
    write_leads(drop, [
        ['  Alice  ', '9876543210', 'P1', '01-Dec-2026', '₹1,234.565', 'HI'],
        ['', '', '', '', '', ''],
        ['Bob', '8876543210', 'P2', 'soon', '-1', 'Hindi'],
        ['', 'bad', '', 'soon', '', 'Hindi'],
        ['Rejected Customer', 'bad', 'P3', 'soon', '', 'Hindi'],
        ['Rejected Customer', '7876543210', '', '', '', ''],
        ['Rejected Customer', '', 'P4', '', '', ''],
    ])
    write_leads(drop, [['ORD-1', 'Feedback Customer', '6876543210', 'Phone', '02/09/2026', '', 'ignored']],
                workflow='policy_feedback', headers=['Order ID','Name','Contact','Item','Purchase Date','Language','extra'])
    result = ingest_leads(connection, privacy, drop)
    assert result == dict(scope='leads_only', imported_files=2, skipped_files=0,
                          lead_rows_total=7, lead_rows_rejected=4, duplicate_lead_rows_merged=0, field_warnings=3)
    records = connection.execute('SELECT * FROM leads ORDER BY workflow_id,id').fetchall()
    assert len(records) == 3
    alice, bob, feedback = [privacy.decrypt(record['values_encrypted']) for record in records]
    assert alice == dict(customer_name='Alice',phone='+919876543210',policy_number='P1',
                         policy_expiry='2026-12-01',premium_amount='1234.57',preferred_language='hi')
    assert bob['policy_expiry'] is None and bob['premium_amount'] is None and bob['preferred_language'] is None
    assert feedback['order_id'] == 'ORD-1' and feedback['order_date'] == '2026-09-02'
    assert apply_defaults(load_schemas()['policy_feedback']['fields'], feedback)['preferred_language'] == 'en'
    rejected = connection.execute('SELECT row_number,reason FROM rejections ORDER BY row_number').fetchall()
    assert [tuple(row) for row in rejected] == [(3,'missing_required:customer_name'), (4,'invalid_phone'),
                                               (5,'missing_required:policy_number'), (6,'missing_required:phone')]
    stored_stats = [json.loads(row[0]) for row in connection.execute('SELECT stats FROM sources')]
    for name in ('lead_rows_total','lead_rows_rejected','field_warnings','duplicate_lead_rows_merged'):
        assert sum(stats[name] for stats in stored_stats) == result[name]
    raw = (tmp_path/'db.sqlite3').read_bytes()
    for secret in (b'Alice', b'Feedback Customer', b'Rejected Customer', b'9876543210'):
        assert secret not in raw


def test_merge_preserves_batch_non_null_fields_and_defaults(store, tmp_path):
    connection, privacy = store
    first, second = tmp_path/'drop_1', tmp_path/'drop_2'
    # Create files in reverse order: filenames, not directory creation, govern merges.
    write_leads(first, [['New Name','+91 98765 43210','P2','','','']], batch='batch_002')
    write_leads(first, [['First Name','9876543210','P1','01/12/2026','12.34','HI']], batch='batch_001')
    write_leads(second, [['TA','Latest Name','P3','09876543210','','']], batch='batch_003',
                headers=['Language','Insured Name','Policy No','Mobile__ No','Expiry Date','Premium'])
    result = ingest_leads(connection, privacy, first)
    assert result['duplicate_lead_rows_merged'] == 1
    record = connection.execute('SELECT * FROM leads').fetchone()
    values = privacy.decrypt(record['values_encrypted'])
    assert record['batch_id'] == 'batch_001'
    assert values['customer_name'] == 'New Name' and values['policy_number'] == 'P2'
    assert values['preferred_language'] == 'hi' and values['premium_amount'] == '12.34'
    assert values['policy_expiry'] == '2026-12-01'
    assert ingest_leads(connection, privacy, second)['duplicate_lead_rows_merged'] == 1
    record = connection.execute('SELECT * FROM leads').fetchone()
    values = privacy.decrypt(record['values_encrypted'])
    assert record['batch_id'] == 'batch_001' and values['preferred_language'] == 'ta'
    assert values['customer_name'] == 'Latest Name' and values['policy_number'] == 'P3'


def test_reimport_skips_records_and_counters_and_ignores_events(store, tmp_path):
    connection, privacy = store
    drop = tmp_path/'drop'
    write_leads(drop, [['Name','9876543210','P1','','','']])
    (drop/'events').mkdir()
    event_path = drop/'events'/'events_0001.jsonl'
    event_path.write_text('intentionally invalid event file: out of scope\n')
    ingest_leads(connection, privacy, drop)
    before = list(connection.iterdump())
    result = ingest_leads(connection, privacy, drop)
    assert result == dict(scope='leads_only',imported_files=0,skipped_files=1,
                          lead_rows_total=0,lead_rows_rejected=0,duplicate_lead_rows_merged=0,field_warnings=0)
    assert before == list(connection.iterdump())
    assert connection.execute('SELECT count(*) FROM events').fetchone()[0] == 0
    assert [row[0] for row in connection.execute('SELECT path FROM sources')] == ['leads/motor_renewal/batch_001.csv']
    assert event_path.read_text() == 'intentionally invalid event file: out of scope\n'


def test_same_phone_is_separate_in_each_workflow(store, tmp_path):
    connection, privacy = store
    drop = tmp_path/'drop'
    write_leads(drop, [['Name','9876543210','P1','','','']])
    write_leads(drop, [['Name','9876543210','ORD1']],workflow='policy_feedback',
                headers=['Name','Contact','Order ID'])
    assert ingest_leads(connection, privacy, drop)['duplicate_lead_rows_merged'] == 0
    assert connection.execute('SELECT count(*) FROM leads').fetchone()[0] == 2


def test_invalid_later_optional_values_do_not_erase_previous_values(store, tmp_path):
    connection, privacy = store
    first, second = tmp_path/'first', tmp_path/'second'
    write_leads(first, [['Name','9876543210','P1','01/12/2026','10.00','HI']])
    write_leads(second, [['Name','9876543210','P1','soon','-1','Hindi']], batch='batch_003')
    ingest_leads(connection, privacy, first)
    result = ingest_leads(connection, privacy, second)
    assert result['field_warnings'] == 3
    record = connection.execute('SELECT values_encrypted FROM leads').fetchone()
    values = privacy.decrypt(record[0])
    assert values['policy_expiry'] == '2026-12-01'
    assert values['premium_amount'] == '10.00' and values['preferred_language'] == 'hi'


def test_bad_later_file_rolls_back_and_retry_succeeds(store, tmp_path):
    connection, privacy = store
    drop = tmp_path/'drop'
    write_leads(drop, [['Name','9876543210','P1','','','']])
    bad = write_leads(drop, [['Name','8876543210','P2','','','']], batch='batch_002')
    bad.write_text('customer_name,phone,policy_number\n"unfinished')
    with pytest.raises(ValueError, match='CSV structure'):
        ingest_leads(connection, privacy, drop)
    for table in ('sources','leads','rejections'):
        assert connection.execute(f'SELECT count(*) FROM {table}').fetchone()[0] == 0
    write_leads(drop, [['Name','8876543210','P2','','','']], batch='batch_002')
    assert ingest_leads(connection, privacy, drop)['imported_files'] == 2
    assert connection.execute('SELECT count(*) FROM leads').fetchone()[0] == 2


def test_changed_source_rolls_back_other_new_files(store, tmp_path):
    connection, privacy = store
    drop = tmp_path/'drop'
    original = write_leads(drop, [['Name','9876543210','P2','','','']], batch='batch_002')
    ingest_leads(connection, privacy, drop)
    before = list(connection.iterdump())
    write_leads(drop, [['Other','8876543210','P1','','','']], batch='batch_001')
    original.write_text(original.read_text()+'Other,7876543210,P3,,,\n')
    with pytest.raises(ValueError, match='file changed'):
        ingest_leads(connection, privacy, drop)
    assert before == list(connection.iterdump())


@pytest.mark.parametrize('contents', [
    'name,customer_name,phone,policy_number\nName,Other,9876543210,P1\n',
    'customer_name,phone,policy_number\nName,9876543210,P1,EXTRA\n',
])
def test_ambiguous_or_broken_columns_fail_without_pii_errors(store, tmp_path, contents):
    connection, privacy = store
    path = write_leads(tmp_path/'drop', [])
    path.write_text(contents)
    with pytest.raises(ValueError) as caught:
        ingest_leads(connection, privacy, tmp_path/'drop')
    assert '9876543210' not in str(caught.value)
    assert connection.execute('SELECT count(*) FROM sources').fetchone()[0] == 0


def test_parent_directory_matches_sequential_imports(store, tmp_path):
    connection, privacy = store
    data = tmp_path/'data'
    write_leads(data/'drop_1', [['Name','9876543210','P1','','','HI']])
    write_leads(data/'drop_2', [['Later','9876543210','P2','','','']],batch='batch_003')
    ingest_leads(connection, privacy, data/'drop_1')
    ingest_leads(connection, privacy, data/'drop_2')
    initialize(tmp_path/'other.sqlite3',tmp_path/'other.keys')
    other, other_privacy = open_database(tmp_path/'other.sqlite3',tmp_path/'other.keys')
    try:
        ingest_leads(other,other_privacy,data)
        def snapshot(conn, crypto):
            return [(row['workflow_id'],row['batch_id'],crypto.decrypt(row['values_encrypted']))
                    for row in conn.execute('SELECT * FROM leads ORDER BY id')]
        assert snapshot(connection,privacy) == snapshot(other,other_privacy)
        assert [tuple(r) for r in connection.execute('SELECT * FROM sources ORDER BY path')] == [tuple(r) for r in other.execute('SELECT * FROM sources ORDER BY path')]
    finally:
        other.close()


def test_cli_leads_only_stays_available_when_full_ingestion_is_enabled(tmp_path):
    drop = tmp_path/'drop'
    write_leads(drop,[['Name','9876543210','P1','','','']])
    db, keys = tmp_path/'db',tmp_path/'keys'
    initialize(db,keys)
    base = [sys.executable,'-m','solution','ingest',str(drop),'--db',str(db),'--key-file',str(keys)]
    imported = subprocess.run([*base,'--leads-only'],capture_output=True,text=True)
    assert imported.returncode == 0, imported.stderr
    assert json.loads(imported.stdout)['lead_rows_total'] == 1
    full = subprocess.run(base,capture_output=True,text=True)
    assert full.returncode == 0, full.stderr
    assert json.loads(full.stdout)['scope'] == 'leads_and_events'
    with sqlite3.connect(db) as connection:
        assert connection.execute('SELECT count(*) FROM events').fetchone()[0] == 0


def test_empty_inputs_and_missing_required_headers(store,tmp_path):
    connection,privacy = store
    drop=tmp_path/'drop'
    write_leads(drop,[['   '],['Actual customer']],headers=['customer_name'])
    result=ingest_leads(connection,privacy,drop)
    assert result['lead_rows_total'] == 1 and result['lead_rows_rejected'] == 1
    assert connection.execute('SELECT reason FROM rejections').fetchone()[0] == 'missing_required:phone'
