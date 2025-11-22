import sqlite3
import os

# -----------------------------------------
# New: Track DB version for future upgrades
# -----------------------------------------
TARGET_SCHEMA_VERSION = 1

SCHEMA_BASE = """
CREATE TABLE IF NOT EXISTS schema_version (
  version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chats (
  id TEXT PRIMARY KEY,
  project_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  created_at TEXT NOT NULL,
  last_used TEXT NOT NULL,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY,
  chat_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  ts TEXT NOT NULL,
  FOREIGN KEY(chat_id) REFERENCES chats(id)
);

CREATE TABLE IF NOT EXISTS distilled (
  id INTEGER PRIMARY KEY,
  project_name TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  summary TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(chat_id) REFERENCES chats(id)
);

CREATE TABLE IF NOT EXISTS debug_log (
  id INTEGER PRIMARY KEY,
  chat_id TEXT NOT NULL,
  info TEXT NOT NULL,
  ts TEXT NOT NULL,
  FOREIGN KEY(chat_id) REFERENCES chats(id)
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""

def apply_migrations(conn):
    """
    Automatic schema upgrades without breaking old DBs.
    Currently handles:
    - creating schema_version if missing
    - setting version = 1
    """
    cur = conn.cursor()

    # Does schema_version table exist?
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    exists = cur.fetchone()

    if not exists:
        # Fresh DB → create version entry
        cur.execute("CREATE TABLE schema_version (version INTEGER NOT NULL)")
        cur.execute("INSERT INTO schema_version(version) VALUES (?)", (TARGET_SCHEMA_VERSION,))
        conn.commit()
        return

    # Check current version
    cur.execute("SELECT version FROM schema_version")
    row = cur.fetchone()

    if not row:
        cur.execute("INSERT INTO schema_version(version) VALUES (1)")
        conn.commit()
        return

    version = row[0]

    # Future migrations go here:
    # if version == 1:
    #     ... migrate to version 2 ...
    #     cur.execute("UPDATE schema_version SET version=2")
    #     conn.commit()

def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    new_db = not os.path.exists(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")   # Enforce referential integrity

    if new_db:
        # Brand-new DB → initialize all schema
        conn.executescript(SCHEMA_BASE)
        conn.commit()

    # Apply migrations even on new DB (safe-op)
    apply_migrations(conn)

    conn.close()

class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")  # ensure during runtime too
        return conn
