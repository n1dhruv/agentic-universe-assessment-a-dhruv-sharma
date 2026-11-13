import sqlite3
import pytest
from solution.storage import initialize, open_database


def test_storage_privacy_and_ledger(tmp_path):
    db, keys = tmp_path/'db.sqlite3', tmp_path/'keys.json'
    initialize(db, keys)
    original = keys.read_bytes()
    initialize(db, keys)
    assert keys.read_bytes() == original
    assert keys.stat().st_mode & 0o777 == 0o600
    connection, privacy = open_database(db, keys)
    value = {'name': 'Private Name Example', 'phone': '+919876543210'}
    encrypted = privacy.encrypt(value)
    assert privacy.decrypt(encrypted) == value
    assert privacy.phone_token(value['phone']) == privacy.phone_token(value['phone'])
    with connection:
        connection.execute('INSERT INTO events VALUES (?,?)', ('event1', encrypted))
    for sql in ["UPDATE events SET body_encrypted='x'", 'DELETE FROM events']:
        with pytest.raises(sqlite3.IntegrityError, match='append-only'):
            connection.execute(sql)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute('INSERT INTO events VALUES (?,?)', ('event1', encrypted))
    connection.close()
    raw = db.read_bytes()
    assert b'Private Name Example' not in raw and b'9876543210' not in raw
    connection, privacy = open_database(db, keys)
    assert privacy.decrypt(connection.execute('SELECT body_encrypted FROM events').fetchone()[0]) == value
    connection.close()


def test_wrong_or_missing_keys_do_not_change_database(tmp_path):
    db, keys = tmp_path/'db', tmp_path/'keys'
    initialize(db, keys)
    initialize(tmp_path/'other', tmp_path/'wrong')
    before = db.read_bytes()
    for key in [tmp_path/'missing', tmp_path/'wrong']:
        with pytest.raises(ValueError):
            initialize(db, key)
        assert db.read_bytes() == before
    assert not (tmp_path/'missing').exists()


def test_transaction_rolls_back_all_changes(tmp_path):
    db, keys = tmp_path/'db', tmp_path/'keys'
    initialize(db, keys)
    connection, privacy = open_database(db, keys)
    with pytest.raises(RuntimeError):
        with connection:
            connection.execute('INSERT INTO sources VALUES (?,?,?)', ('input.csv', 'digest', '{}'))
            connection.execute('INSERT INTO events VALUES (?,?)', ('event', privacy.encrypt({'phone': '+919876543210'})))
            raise RuntimeError('simulated interruption')
    assert connection.execute('SELECT count(*) FROM sources').fetchone()[0] == 0
    assert connection.execute('SELECT count(*) FROM events').fetchone()[0] == 0
    connection.close()
