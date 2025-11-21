# core/services/message_service.py
from datetime import datetime, UTC
from core.db.database import Database


class MessageService:
    def __init__(self, db: Database):
        self.db = db

    def _now(self):
        # timezone-aware UTC with trailing Z
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def add_message(self, chat_id, role, content):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages(chat_id, role, content, ts) "
            "VALUES (?, ?, ?, ?)",
            (chat_id, role, content, self._now())
        )
        conn.commit()
        conn.close()

    def last_messages(self, chat_id, limit=20):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT role, content, ts FROM messages "
            "WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
            (chat_id, limit)
        )
        rows = cur.fetchall()
        conn.close()
        # newest first → reverse for chronological order
        return list(reversed(rows))

    def get_messages(self, chat_id):
        """Fetch all messages for a chat in chronological order."""
        conn = self.db.connect()
        cur = conn.execute(
            "SELECT role, content, ts FROM messages "
            "WHERE chat_id=? ORDER BY id ASC",
            (chat_id,)
        )
        rows = cur.fetchall()
        conn.close()
        return rows
