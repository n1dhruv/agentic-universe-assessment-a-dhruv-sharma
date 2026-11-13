"""Event ledger, quarantine, transactional import, and late-linking contracts."""

import csv
from datetime import timezone
import json
import subprocess
import sys

import pytest

from solution.events import load_catalogue, quality_summary, resolve_events, timestamp
from solution.ingest import ingest
from solution.leads import ingest_leads
from solution.storage import initialize, open_database


def write_lead(drop, phone='9876543210', workflow='motor_renewal', batch='batch_001'):
    path = drop/'leads'/workflow/(batch+'.csv')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['customer_name','phone','policy_number' if workflow=='motor_renewal' else 'order_id'])
        writer.writerow(['Private Test Customer',phone,'REF1'])
    return path


def event(event_id, kind='call.initiated', call='c1', phone='9876543210',
          time='2026-10-01T18:29:00Z', code=None, workflow='motor_renewal'):
    value = dict(event_id=event_id,event_type=kind,call_id=call,workflow_id=workflow,
                 occurred_at=time,payload={})
    if phone is not None:
        value['phone'] = phone
    if code is not None:
        value['payload']['disposition_code'] = code
    return value


def write_events(drop, events, filename='events_0001.jsonl'):
    path = drop/'events'/filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('\n'.join(item if isinstance(item,str) else json.dumps(item) for item in events)+'\n')
    return path


@pytest.fixture
def store(tmp_path):
    db, keys = tmp_path/'db.sqlite3',tmp_path/'keys.json'
    initialize(db,keys)
    connection,privacy = open_database(db,keys)
    yield connection,privacy
    connection.close()


@pytest.mark.parametrize('raw', ['2026-10-01T18:29:00Z','2026-10-01T23:59:00+05:30',
                                '2026-10-01 23:59:00','2026-10-01T14:29:00-04:00'])
def test_timestamp_forms_are_same_utc_instant(raw):
    assert timestamp(raw) == timestamp('2026-10-01T18:29:00Z')
    assert timestamp(raw).tzinfo is timezone.utc


@pytest.mark.parametrize('raw', ['tomorrow','2026-02-31T12:00:00Z',None,123,'2026-10-01'])
def test_bad_timestamps_fail(raw):
    with pytest.raises(ValueError):
        timestamp(raw)


def test_malformed_and_duplicate_precede_other_classifications(store,tmp_path):
    connection,privacy=store
    drop=tmp_path/'drop'
    write_lead(drop)
    first=event('same')
    # The duplicate body has no timestamp or other structural fields. It must be
    # ignored as a duplicate, rather than failing validation or replacing the first.
    write_events(drop,[first,{'event_id':'same'},'{broken',{},[],
                       '{"event_id":"nan","payload":{"n":NaN}}','  ','',
                       event('orphan',phone='bad'),
                       event('unknown','disposition.set',code='RENEWD')])
    result=ingest(connection,privacy,drop)
    assert result['events_total']==8
    assert result['malformed_events']==4 and result['duplicate_events_dropped']==1
    assert connection.execute('SELECT count(*) FROM events').fetchone()[0]==3
    assert result['event_state']==dict(eligible_events=1,orphan_events=1,unknown_disposition_events=1)
    saved=connection.execute("SELECT body_encrypted FROM events WHERE event_id='same'").fetchone()[0]
    assert privacy.decrypt(saved)==first
    raw=(tmp_path/'db.sqlite3').read_bytes()
    assert b'Private Test Customer' not in raw and b'9876543210' not in raw


def test_late_lead_resolves_orphans_and_reclassifies_unknown_code(store,tmp_path):
    connection,privacy=store
    first,second=tmp_path/'drop_1',tmp_path/'drop_2'
    write_events(first,[event('a-override','disposition.override',phone=None,code='renewed'),
                        event('b-start'),event('c-unknown','disposition.set',code='RENEWD'),
                        event('d-never-linked',phone='8876543210')])
    one=ingest(connection,privacy,first)
    assert one['event_state']==dict(eligible_events=0,orphan_events=4,unknown_disposition_events=0)
    encrypted_before=[tuple(row) for row in connection.execute('SELECT * FROM events ORDER BY event_id')]
    write_lead(second,batch='batch_003')
    two=ingest(connection,privacy,second)
    assert two['event_state']==dict(eligible_events=2,orphan_events=1,unknown_disposition_events=1)
    resolved=resolve_events(connection,privacy)
    assert {item.event_id for item in resolved.eligible}=={'a-override','b-start'}
    assert len({item.lead_id for item in resolved.eligible})==1
    assert resolved.quarantined=={'c-unknown':'unknown_disposition','d-never-linked':'orphan'}
    assert encrypted_before==[tuple(row) for row in connection.execute('SELECT * FROM events ORDER BY event_id')]
    before=list(connection.iterdump())
    assert quality_summary(connection,privacy)['events_total']==4
    assert before==list(connection.iterdump())


def test_override_can_wait_for_later_call_event_without_initiation(store,tmp_path):
    connection,privacy=store
    first,second=tmp_path/'drop_1',tmp_path/'drop_2'
    write_lead(first)
    write_events(first,[event('override','disposition.override',phone=None,code='renewed')])
    assert ingest(connection,privacy,first)['event_state']['orphan_events']==1
    # Linking needs another event on the call, not necessarily initiation. Phase 5
    # will separately require initiation before counting a call in reports.
    write_events(second,[event('connected','call.connected')],filename='events_1001.jsonl')
    assert ingest(connection,privacy,second)['event_state']['eligible_events']==2


def test_workflow_scopes_call_links_and_catalogue(store,tmp_path):
    connection,privacy=store
    drop=tmp_path/'drop'
    write_lead(drop)
    write_lead(drop,phone='8876543210',workflow='policy_feedback')
    write_events(drop,[event('motor-start'),
                       event('feedback-start',phone='8876543210',workflow='policy_feedback'),
                       event('feedback-override','disposition.override',phone=None,code='feedback_captured',workflow='policy_feedback'),
                       event('motor-wrong-code','disposition.set',code='feedback_captured'),
                       event('unknown-workflow',workflow='unregistered'),
                       event('missing-phone',phone=None)])
    result=ingest(connection,privacy,drop)
    assert result['event_state']==dict(eligible_events=3,orphan_events=2,unknown_disposition_events=1)
    resolved=resolve_events(connection,privacy)
    owners={item.event_id:item.lead_id for item in resolved.eligible}
    assert owners['feedback-start']==owners['feedback-override']!=owners['motor-start']


def test_ambiguous_call_owner_does_not_guess_override_link(store,tmp_path):
    connection,privacy=store
    drop=tmp_path/'drop'
    write_lead(drop)
    write_lead(drop,phone='8876543210',batch='batch_002')
    write_events(drop,[event('one'),event('two',phone='8876543210'),
                       event('override','disposition.override',phone=None,code='renewed')])
    result=ingest(connection,privacy,drop)
    assert result['event_state']==dict(eligible_events=2,orphan_events=1,unknown_disposition_events=0)
    assert resolve_events(connection,privacy).quarantined['override']=='orphan'


@pytest.mark.parametrize('code',[None,'not_in_catalogue',['renewed']])
def test_missing_or_unknown_disposition_is_excluded_but_retained(store,tmp_path,code):
    connection,privacy=store
    drop=tmp_path/'drop'
    write_lead(drop)
    write_events(drop,[event('start'),event('outcome','disposition.set',code=code)])
    result=ingest(connection,privacy,drop)
    assert result['event_state']==dict(eligible_events=1,orphan_events=0,unknown_disposition_events=1)
    assert [item.event_id for item in resolve_events(connection,privacy).eligible]==['start']
    assert connection.execute('SELECT count(*) FROM events').fetchone()[0]==2


@pytest.mark.parametrize('change',[
    {'occurred_at':'tomorrow'}, {'workflow_id':None}, {'event_type':'unsupported'},
    {'payload':[]}, {'call_id':[]},
])
def test_structural_failures_roll_back_entire_drop_and_retry(store,tmp_path,change):
    connection,privacy=store
    drop=tmp_path/'drop'
    write_lead(drop)
    bad=event('bad'); bad.update(change)
    write_events(drop,[event('valid'),bad])
    with pytest.raises(ValueError,match='Unsupported event structure') as caught:
        ingest(connection,privacy,drop)
    assert '9876543210' not in str(caught.value)
    for table in ('sources','leads','events','rejections'):
        assert connection.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==0
    write_events(drop,[event('valid'),event('fixed')])
    result=ingest(connection,privacy,drop)
    assert result['event_state']['eligible_events']==2


def test_repeat_and_cross_drop_duplicate_preserve_first_body_and_counts(store,tmp_path):
    connection,privacy=store
    first,second=tmp_path/'drop_1',tmp_path/'drop_2'
    write_lead(first)
    original=event('id1')
    write_events(first,[original])
    ingest(connection,privacy,first)
    write_events(second,[event('id1',phone='8876543210'),event('id2','call.connected')],filename='events_1001.jsonl')
    result=ingest(connection,privacy,second)
    assert result['duplicate_events_dropped']==1
    assert result['quality']['events_total']==3
    assert result['quality']['duplicate_events_dropped']==1
    assert result['event_state']['eligible_events']==2
    saved=connection.execute("SELECT body_encrypted FROM events WHERE event_id='id1'").fetchone()[0]
    assert privacy.decrypt(saved)==original
    before=list(connection.iterdump())
    repeated=ingest(connection,privacy,tmp_path)
    assert repeated['imported_files']==0 and repeated['skipped_files']==3
    assert repeated['events_total']==0 and repeated['quality']==result['quality']
    assert before==list(connection.iterdump())


def test_upgrade_lead_only_database_without_recounting_customers(store,tmp_path):
    connection,privacy=store
    drop=tmp_path/'drop'
    write_lead(drop)
    write_events(drop,[event('start')])
    ingest_leads(connection,privacy,drop)
    result=ingest(connection,privacy,drop)
    assert result['skipped_files']==1 and result['imported_files']==1
    assert result['lead_rows_total']==0 and result['quality']['lead_rows_total']==1
    assert result['quality']['duplicate_lead_rows_merged']==0
    assert result['events_total']==1


def test_changed_event_file_rolls_back_new_leads(store,tmp_path):
    connection,privacy=store
    drop=tmp_path/'drop'
    path=write_events(drop,[event('start')])
    ingest(connection,privacy,drop)
    before=list(connection.iterdump())
    write_lead(drop)
    path.write_text(path.read_text()+json.dumps(event('new'))+'\n')
    with pytest.raises(ValueError,match='event file changed'):
        ingest(connection,privacy,drop)
    assert before==list(connection.iterdump())


def test_parent_and_sequential_runs_produce_same_events_and_quality(store,tmp_path):
    connection,privacy=store
    data=tmp_path/'data'
    write_events(data/'drop_1',[event('start'),event('override','disposition.override',phone=None,code='renewed')])
    write_lead(data/'drop_2',batch='batch_003')
    write_events(data/'drop_2',[event('connected','call.connected'),event('start')],filename='events_1001.jsonl')
    ingest(connection,privacy,data/'drop_1')
    ingest(connection,privacy,data/'drop_2')
    initialize(tmp_path/'other',tmp_path/'other.keys')
    other,other_privacy=open_database(tmp_path/'other',tmp_path/'other.keys')
    try:
        ingest(other,other_privacy,data)
        assert resolve_events(connection,privacy)==resolve_events(other,other_privacy)
        assert quality_summary(connection,privacy)==quality_summary(other,other_privacy)
        assert [tuple(r) for r in connection.execute('SELECT * FROM sources ORDER BY path')]==[
            tuple(r) for r in other.execute('SELECT * FROM sources ORDER BY path')]
    finally:
        other.close()


def test_quality_and_catalogue_contract(store,tmp_path):
    connection,privacy=store
    drop=tmp_path/'drop'
    write_lead(drop)
    write_lead(drop,phone='bad',batch='batch_002')
    write_events(drop,[event('start'),'{invalid',event('start')])
    ingest(connection,privacy,drop)
    assert quality_summary(connection,privacy)=={
        'lead_rows_total':2,'lead_rows_rejected':1,'duplicate_lead_rows_merged':0,'field_warnings':0,
        'events_total':3,'malformed_events':1,'duplicate_events_dropped':1,
        'rejections_by_reason':{'invalid_phone':1},'orphan_events':0,'unknown_disposition_events':0,
    }
    assert load_catalogue()['motor_renewal','renewed']=={'is_terminal':True,'is_success':True}


def test_cli_full_import_and_reopen(store,tmp_path):
    connection,privacy=store
    drop=tmp_path/'drop'
    write_lead(drop)
    write_events(drop,[event('start')])
    result=subprocess.run([sys.executable,'-m','solution','ingest',str(drop),
                           '--db',str(tmp_path/'db.sqlite3'),'--key-file',str(tmp_path/'keys.json')],
                          capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['event_state']['eligible_events']==1
    assert '9876543210' not in result.stdout
    reopened,crypto=open_database(tmp_path/'db.sqlite3',tmp_path/'keys.json')
    try:
        assert resolve_events(reopened,crypto).counts['eligible_events']==1
    finally:
        reopened.close()
