# core/services/settings_service.py

import datetime
from core.db.database import Database

class SettingsService:
    def __init__(self, db: Database):
        self.db = db
        self._ensure_table()

    def _now(self):
        return datetime.datetime.now(datetime.UTC).isoformat()

    def _ensure_table(self):
        conn = self.db.connect()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def get(self, key, default=None):
        conn = self.db.connect()
        cur = conn.execute(
            "SELECT value FROM settings WHERE key = ?",
            (key,)
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return default
        v = row[0]
        if v == "true":
            return True
        if v == "false":
            return False
        return v

    def set(self, key, value):
        if isinstance(value, bool):
            value = "true" if value else "false"
        conn = self.db.connect()
        conn.execute(
            "REPLACE INTO settings(key, value, updated_at) VALUES (?,?,?)",
            (key, value, self._now())
        )
        conn.commit()
        conn.close()

    def toggle(self, key, default=False):
        current = self.get(key, default)
        new_val = not bool(current)
        self.set(key, new_val)
        return new_val
