"""SQLite storage and authenticated encryption. Keys never enter the database."""

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3

from cryptography.fernet import Fernet, InvalidToken

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sources (
    path TEXT PRIMARY KEY, digest TEXT NOT NULL, stats TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY, workflow_id TEXT NOT NULL, phone_token TEXT NOT NULL,
    batch_id TEXT NOT NULL, values_encrypted TEXT NOT NULL,
    UNIQUE(workflow_id, phone_token)
);
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY, body_encrypted TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rejections (
    source_path TEXT NOT NULL REFERENCES sources(path), workflow_id TEXT NOT NULL,
    batch_id TEXT NOT NULL, row_number INTEGER NOT NULL, reason TEXT NOT NULL,
    PRIMARY KEY(source_path, row_number)
);
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
BEGIN SELECT RAISE(ABORT, 'Event ledger is append-only'); END;
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'Event ledger is append-only'); END;
"""


class Privacy:
    def __init__(self, encryption_key, matching_key):
        self.cipher = Fernet(encryption_key.encode())
        self.matching_key = base64.urlsafe_b64decode(matching_key.encode())
        if len(self.matching_key) != 32:
            raise ValueError("Invalid matching key")
        self.key_id = hashlib.sha256((encryption_key + matching_key).encode()).hexdigest()

    def encrypt(self, value):
        return self.cipher.encrypt(json.dumps(value, ensure_ascii=False).encode()).decode()

    def decrypt(self, value):
        try:
            return json.loads(self.cipher.decrypt(value.encode()))
        except InvalidToken:
            raise ValueError("Unable to decrypt stored data with these keys") from None

    def phone_token(self, phone):
        return hmac.new(self.matching_key, phone.encode(), hashlib.sha256).hexdigest()


def load_privacy(key_file):
    try:
        values = json.loads(Path(key_file).read_text())
        return Privacy(values['encryption'], values['matching'])
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError("Missing or invalid key file; use the original keys or initialize a new database") from None


def connect(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys = ON')
    return connection


def initialize(db, key_file):
    db, key_file = Path(db), Path(key_file)
    if db.resolve() == key_file.resolve():
        raise ValueError('Database and key file must have different paths')
    if db.exists():
        connection, _ = open_database(db, key_file)
        connection.close()
        return
    if not key_file.exists():
        key_file.parent.mkdir(parents=True, exist_ok=True)
        values = {'encryption': Fernet.generate_key().decode(),
                  'matching': base64.urlsafe_b64encode(os.urandom(32)).decode()}
        with open(os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
            json.dump(values, stream)
    privacy = load_privacy(key_file)
    db.parent.mkdir(parents=True, exist_ok=True)
    connection = connect(db)
    try:
        connection.executescript(SCHEMA)
        with connection:
            connection.execute('INSERT INTO metadata VALUES (?,?)', ('key_id', privacy.key_id))
    finally:
        connection.close()


def open_database(db, key_file):
    privacy = load_privacy(key_file)
    if not Path(db).is_file():
        raise ValueError('Database does not exist; run init first')
    # mode=rw prevents accidental database creation on a mistaken path.
    connection = sqlite3.connect(Path(db).resolve().as_uri() + '?mode=rw', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute('PRAGMA foreign_keys = ON')
        record = connection.execute("SELECT value FROM metadata WHERE key='key_id'").fetchone()
        if record is None or not hmac.compare_digest(record['value'], privacy.key_id):
            raise ValueError('Keys do not match this database; use its original key file')
    except Exception:
        connection.close()
        raise
    return connection, privacy
