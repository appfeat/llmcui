# core/services/settings_service.py
import sqlite3
from core.db.database import Database


class SettingsService:
    def __init__(self, db: Database):
        self.db = db

    def get(self, key, default=None):
        conn = self.db.connect()
        cur = conn.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        conn.close()
        return row["value"] if row else default

    def get_bool(self, key, default=False):
        """Return setting as boolean. Accepts: 1, 0, true, false, yes, no."""
        val = self.get(key, None)
        if val is None:
            return default
        val = str(val).strip().lower()
        if val in ("1", "true", "yes", "on"):
            return True
        if val in ("0", "false", "no", "off"):
            return False
        return default

    def set(self, key, value):
        value = str(value)
        conn = self.db.connect()
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()
        conn.close()

    def toggle(self, key, default=False):
        """Flip boolean stored as text. Returns new value."""
        current = self.get_bool(key, default)
        new_value = not current
        self.set(key, "1" if new_value else "0")
        return new_value
