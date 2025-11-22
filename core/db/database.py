import sqlite3
import os

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS chats (
  id TEXT PRIMARY KEY,
  project_id INTEGER,
  title TEXT,
  created_at TEXT,
  last_used TEXT,
  FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY,
  chat_id TEXT,
  role TEXT,
  content TEXT,
  ts TEXT
);

CREATE TABLE IF NOT EXISTS distilled (
  id INTEGER PRIMARY KEY,
  project_name TEXT,
  chat_id TEXT,
  summary TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS debug_log (
  id INTEGER PRIMARY KEY,
  chat_id TEXT,
  info TEXT,
  ts TEXT
);

CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);
"""

def init_db(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)   # ← ALWAYS apply schema
    conn.commit()
    conn.close()


class Database:
    def __init__(self, db_path):
        self.db_path = db_path

    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn
