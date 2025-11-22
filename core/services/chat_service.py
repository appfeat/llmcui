from datetime import datetime, UTC
import uuid
from core.db.database import Database


class ChatService:
    def __init__(self, db: Database):
        self.db = db

    def _now(self):
        # timezone-aware UTC with trailing Z
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def get_or_create_first(self, project_name):
        conn = self.db.connect()
        cur = conn.cursor()

        # ensure project exists
        cur.execute("SELECT id FROM projects WHERE name = ?", (project_name,))
        p = cur.fetchone()

        if not p:
            cur.execute(
                "INSERT INTO projects(name, created_at) VALUES (?, ?)",
                (project_name, self._now())
            )
            conn.commit()
            cur.execute("SELECT id FROM projects WHERE name = ?", (project_name,))
            p = cur.fetchone()

        project_id = p[0]

        # try to get most recent chat
        cur.execute(
            "SELECT id FROM chats WHERE project_id = ? "
            "ORDER BY last_used DESC LIMIT 1",
            (project_id,)
        )
        r = cur.fetchone()

        if r:
            chat_id = r[0]
            cur.execute(
                "UPDATE chats SET last_used=? WHERE id=?",
                (self._now(), chat_id)
            )
            conn.commit()
            conn.close()
            return chat_id

        # create a new chat
        chat_id = "chat-" + uuid.uuid4().hex[:8]
        cur.execute(
            "INSERT INTO chats(id, project_id, title, created_at, last_used) "
            "VALUES (?, ?, ?, ?, ?)",
            (chat_id, project_id, "(untitled)", self._now(), self._now())
        )
        conn.commit()
        conn.close()
        return chat_id

    def reset_chat(self, chat_id):
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        cur.execute("DELETE FROM distilled WHERE chat_id = ?", (chat_id,))

        conn.commit()
        conn.close()

    def get_distilled_chat(self, chat_id):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT summary FROM distilled "
            "WHERE chat_id = ? ORDER BY created_at DESC LIMIT 1",
            (chat_id,)
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else ""

    def append_archive(self, chat_id, user_text, assistant_text):
        # MVP: archive is implicit via messages table
        return

    def get_messages(self, chat_id):
        """Return all messages in chronological order."""
        conn = self.db.connect()
        cur = conn.execute(
            "SELECT role, content, ts FROM messages "
            "WHERE chat_id=? ORDER BY id ASC",
            (chat_id,)
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    # ---------------------------------------------------------
    # STEP 3: NEW CHAT TITLE LOGIC
    # ---------------------------------------------------------

    def is_new_chat(self, chat_id) -> bool:
        """Return True if chat has zero messages."""
        conn = self.db.connect()
        cur = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE chat_id = ?",
            (chat_id,)
        )
        count = cur.fetchone()[0]
        conn.close()
        return count == 0

    def update_title(self, chat_id, title: str):
        """Update the chat's title."""
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE chats SET title = ?, last_used = ? WHERE id = ?",
            (title, self._now(), chat_id)
        )
        conn.commit()
        conn.close()
