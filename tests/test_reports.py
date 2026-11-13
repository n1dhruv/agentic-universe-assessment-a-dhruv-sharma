"""Independent exact report fixtures and derived-call edge cases."""

import csv
import io
import json
from pathlib import Path
import subprocess
import sys

import pytest

from solution.events import load_catalogue, resolve_events
from solution.ingest import ingest
from solution.reports import HEADERS, build_call_facts, lead_bucket, render_reports, write_reports
from solution.storage import initialize, open_database
from test_events import event, write_events, write_lead


@pytest.fixture
def store(tmp_path):
    db, keys = tmp_path/'db.sqlite3', tmp_path/'keys.json'
    initialize(db, keys)
    connection, privacy = open_database(db, keys)
    yield connection, privacy
    connection.close()


def csv_rows(content):
    return list(csv.DictReader(io.StringIO(content)))


def golden_input(drop):
    path = drop/'leads'/'motor_renewal'/'batch_001.csv'
    path.parent.mkdir(parents=True)
    headers = ['customer_name','phone','policy_number','policy_expiry','premium_amount','preferred_language']
    with path.open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows([
            ['Alice Private','9876543210','A','','',''],
            ['Bob Private','8876543211','B','','',''],
            ['', '', '', '', '', ''],
            ['Cara Private','7876543212','C','','',''],
            ['Dan Private','6876543213','D','','',''],
            ['', 'bad', 'REJECT', 'soon', '', 'Hindi'],
        ])
    with (path.parent/'batch_002.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows([['Eve Private','9876543214','E','soon','Rs.20','Hindi'],
                          ['Alice Updated','+91 98765 43210','A','','','HI']])
    feedback = write_lead(drop,phone='8876543215',workflow='policy_feedback')
    feedback.write_text('customer_name,phone,order_id\nFeedback Private,8876543215,F\n')
    events = []

    def add(key, kind='call.initiated', call='a1', phone='9876543210',
            time='2026-10-02 10:00:00', code=None, workflow='motor_renewal'):
        value = event(key,kind,call,phone,time,code,workflow)
        events.append(value)
        return value

    first = add('a1-start',time='2026-10-01T18:29:00Z')
    add('a1-connect','call.connected',time='2026-10-01T23:59:30+05:30')
    add('a1-set','disposition.set',time='2026-10-02 00:01:00',code='renewed')
    add('a1-override','disposition.override',phone=None,time='2026-10-02 00:02:00',code='not_interested')
    add('a1-late-set','disposition.set',time='2026-10-03 12:00:00',code='renewed')
    add('a2-start',call='a2',time='2026-10-01T18:31:00Z')
    add('a2-connect','call.connected',call='a2',time='2026-10-02 00:01:10')
    add('a2-set','disposition.set',call='a2',time='2026-10-02 00:02:00',code='renewed')
    for number, hour in [(1,10),(2,11)]:
        add(f'b{number}-start',call=f'b{number}',phone='8876543211',time=f'2026-10-02 {hour}:00:00')
        add(f'b{number}-fail','call.telephony_failed',call=f'b{number}',phone='8876543211',time=f'2026-10-02 {hour}:00:10')
    add('c1-start',call='c1',phone='7876543212',time='2026-10-02 12:00:00')
    add('c1-fail','call.telephony_failed',call='c1',phone='7876543212',time='2026-10-02 12:00:10')
    add('c2-start',call='c2',phone='7876543212',time='2026-10-02 13:00:00')
    add('c2-connect','call.connected',call='c2',phone='7876543212',time='2026-10-02 13:00:10')
    add('c2-set','disposition.set',call='c2',phone='7876543212',time='2026-10-02 13:01:00',code='callback_requested')
    add('c3-start',call='c3',phone='7876543212',time='2026-10-03 09:00:00')
    add('d-connect','call.connected',call='d0',phone='6876543213')
    add('d-set','disposition.set',call='d0',phone='6876543213',code='renewed')
    for number, hour in [(1,14),(2,15)]:
        add(f'e{number}-start',call=f'e{number}',phone='9876543214',time=f'2026-10-02 {hour}:00:00')
        add(f'e{number}-connect','call.connected',call=f'e{number}',phone='9876543214',time=f'2026-10-02 {hour}:00:10')
        add(f'e{number}-set','disposition.set',call=f'e{number}',phone='9876543214',time=f'2026-10-02 {hour}:01:00',code='renewed')
    add('f-start',call='f1',phone='8876543215',workflow='policy_feedback')
    add('f-connect','call.connected',call='f1',phone='8876543215',time='2026-10-02 10:00:10',workflow='policy_feedback')
    add('f-set','disposition.set',call='f1',phone='8876543215',time='2026-10-02 10:01:00',code='feedback_captured',workflow='policy_feedback')
    add('unknown','disposition.set',call='a2',code='RENEWD')
    add('orphan-start',call='orphan',phone='9999999999')
    add('orphan-override','disposition.override',call='orphan',phone=None,code='unknown')
    # Reverse delivery order to prove reports use occurrence times, not arrival.
    write_events(drop,[*reversed(events),first,'{broken',''])


def test_all_five_files_match_hand_calculated_fixture(store,tmp_path):
    connection,privacy = store
    golden_input(tmp_path/'drop')
    ingest(connection,privacy,tmp_path/'drop')
    before = list(connection.iterdump())
    write_reports(connection,privacy,tmp_path/'reports')
    expected = Path(__file__).parent/'fixtures'/'report_expected'
    names = [*HEADERS,'data_quality.json']
    assert sorted(path.name for path in (tmp_path/'reports').iterdir()) == sorted(names)
    for name in names:
        assert (tmp_path/'reports'/name).read_bytes() == (expected/name).read_bytes(), name
    assert before == list(connection.iterdump())
    for path in (tmp_path/'reports').iterdir():
        assert b'Private' not in path.read_bytes() and b'9876543210' not in path.read_bytes()


def test_empty_database_writes_headers_and_zero_quality(store,tmp_path):
    connection,privacy = store
    write_reports(connection,privacy,tmp_path/'reports')
    for name, header in HEADERS.items():
        assert (tmp_path/'reports'/name).read_text() == ','.join(header)+'\n'
    quality = json.loads((tmp_path/'reports'/'data_quality.json').read_text())
    assert quality.pop('rejections_by_reason') == {}
    assert len(quality) == 9 and set(quality.values()) == {0}


def test_latest_valid_override_wins_over_newer_set_and_arrival_order(store,tmp_path):
    connection,privacy = store
    drop = tmp_path/'drop'
    write_lead(drop)
    write_events(drop,[event('start'),
        event('set','disposition.set',time='2026-10-10 12:00:00',code='renewed'),
        event('new-override','disposition.override',phone=None,time='2026-10-04 12:00:00',code='callback_requested'),
        event('old-override','disposition.override',phone=None,time='2026-10-03 12:00:00',code='not_interested')])
    ingest(connection,privacy,drop)
    calls = build_call_facts(resolve_events(connection,privacy).eligible,load_catalogue())
    assert len(calls) == 1 and calls[0].disposition == 'callback_requested'
    assert not calls[0].success and lead_bucket(calls) == 'in_progress_dialed'


def test_latest_set_and_timestamp_ties_are_deterministic(store,tmp_path):
    connection,privacy = store
    drop = tmp_path/'drop'
    write_lead(drop)
    write_events(drop,[event('start'),
        event('z-set','disposition.set',time='2026-10-04 12:00:00',code='renewed'),
        event('a-set','disposition.set',time='2026-10-04 12:00:00',code='not_interested'),
        event('old-set','disposition.set',time='2026-10-03 12:00:00',code='callback_requested'),
        event('unknown','disposition.override',phone=None,time='2026-10-05 12:00:00',code='RENEWD')])
    ingest(connection,privacy,drop)
    lead = csv_rows(render_reports(connection,privacy)['lead_report.csv'])[0]
    assert lead['current_disposition'] == 'renewed' and lead['ever_success'] == 'true'


def test_later_override_can_remove_previously_reported_success(store,tmp_path):
    connection,privacy = store
    first,second = tmp_path/'drop_1',tmp_path/'drop_2'
    write_lead(first)
    write_events(first,[event('start'),event('success','disposition.set',code='renewed')])
    ingest(connection,privacy,first)
    initial = render_reports(connection,privacy)
    assert csv_rows(initial['lead_report.csv'])[0]['ever_success'] == 'true'
    assert csv_rows(initial['daily_overview.csv'])[0]['success_leads'] == '1'
    earlier = [tuple(row) for row in connection.execute('SELECT * FROM events ORDER BY event_id')]
    write_events(second,[event('correction','disposition.override',phone=None,time='2026-10-05 12:00:00',code='callback_requested')],filename='events_1001.jsonl')
    ingest(connection,privacy,second)
    corrected = render_reports(connection,privacy)
    lead = csv_rows(corrected['lead_report.csv'])[0]
    assert lead['ever_success'] == 'false' and lead['bucket'] == 'in_progress_dialed'
    assert csv_rows(corrected['daily_overview.csv'])[0]['success_leads'] == '0'
    for event_id,body in earlier:
        assert connection.execute('SELECT body_encrypted FROM events WHERE event_id=?',(event_id,)).fetchone()[0] == body


def test_terminal_outcome_precedes_all_failed_bucket(store,tmp_path):
    connection,privacy = store
    drop = tmp_path/'drop'
    write_lead(drop)
    write_events(drop,[event('start'),event('failed','call.telephony_failed'),
                       event('terminal','disposition.set',code='not_interested')])
    ingest(connection,privacy,drop)
    lead = csv_rows(render_reports(connection,privacy)['lead_report.csv'])[0]
    assert lead['bucket'] == 'completed' and lead['ever_success'] == 'false'


def test_multiple_initiations_count_one_call_using_earliest_time(store,tmp_path):
    connection,privacy = store
    drop = tmp_path/'drop'
    write_lead(drop)
    write_events(drop,[event('later',time='2026-10-03 10:00:00'),
                       event('earlier',time='2026-10-02 10:00:00')])
    ingest(connection,privacy,drop)
    reports = render_reports(connection,privacy)
    lead = csv_rows(reports['lead_report.csv'])[0]
    assert lead['total_calls'] == '1' and lead['last_call_at'] == '2026-10-02T10:00:00+05:30'
    assert csv_rows(reports['daily_overview.csv'])[0]['date'] == '2026-10-02'


def test_equal_reference_sort_uses_phone_not_insertion_order_or_secret_key(store,tmp_path):
    connection,privacy = store
    drop = tmp_path/'drop'
    write_lead(drop,phone='9876542222')
    write_lead(drop,phone='6876541111',batch='batch_002')
    ingest(connection,privacy,drop)
    rows = csv_rows(render_reports(connection,privacy)['lead_report.csv'])
    assert [row['phone_masked'] for row in rows] == ['+91******1111','+91******2222']
    assert [row['batch_id'] for row in rows] == ['batch_002','batch_001']


def test_repeated_reporting_is_byte_identical_and_read_only(store,tmp_path):
    connection,privacy = store
    golden_input(tmp_path/'drop')
    ingest(connection,privacy,tmp_path/'drop')
    before = list(connection.iterdump())
    write_reports(connection,privacy,tmp_path/'reports')
    first = {path.name:path.read_bytes() for path in (tmp_path/'reports').iterdir()}
    write_reports(connection,privacy,tmp_path/'reports')
    assert first == {path.name:path.read_bytes() for path in (tmp_path/'reports').iterdir()}
    assert before == list(connection.iterdump())


def test_staging_failure_keeps_existing_reports_and_cleans_temporary_files(store,tmp_path,monkeypatch):
    connection,privacy = store
    out = tmp_path/'reports'
    write_reports(connection,privacy,out)
    before = {path.name:path.read_bytes() for path in out.iterdir()}
    original_write = Path.write_text
    def fail_staging(path,*args,**kwargs):
        if path.parent.name.startswith('.report-') and path.name == 'daily_overview.csv':
            raise OSError('simulated disk write failure')
        return original_write(path,*args,**kwargs)
    monkeypatch.setattr(Path,'write_text',fail_staging)
    with pytest.raises(OSError,match='simulated disk write failure'):
        write_reports(connection,privacy,out)
    assert before == {path.name:path.read_bytes() for path in out.iterdir()}


@pytest.mark.parametrize('protected',['database','key'])
def test_cli_does_not_overwrite_database_or_key_with_report(tmp_path,protected):
    out = tmp_path/'reports'
    db = out/'lead_report.csv' if protected == 'database' else tmp_path/'db.sqlite3'
    keys = out/'data_quality.json' if protected == 'key' else tmp_path/'keys.json'
    initialize(db,keys)
    before_db,before_keys = db.read_bytes(),keys.read_bytes()
    result = subprocess.run([sys.executable,'-m','solution','report','--out',str(out),
                             '--db',str(db),'--key-file',str(keys)],capture_output=True,text=True)
    assert result.returncode == 1 and 'protected file' in result.stderr
    assert db.read_bytes() == before_db and keys.read_bytes() == before_keys


def test_cli_report_writes_five_files(store,tmp_path):
    connection,privacy = store
    golden_input(tmp_path/'drop')
    ingest(connection,privacy,tmp_path/'drop')
    out = tmp_path/'reports'
    result = subprocess.run([sys.executable,'-m','solution','report','--out',str(out),
                             '--db',str(tmp_path/'db.sqlite3'),'--key-file',str(tmp_path/'keys.json')],
                            capture_output=True,text=True)
    assert result.returncode == 0,result.stderr
    assert result.stdout.strip() == 'Wrote five report files.'
    assert len(list(out.iterdir())) == 5
