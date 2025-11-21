# core/services/project_service.py
from datetime import datetime, UTC
from core.db.database import Database


class ProjectService:
    def __init__(self, db: Database):
        self.db = db

    def _now(self):
        # timezone-aware UTC with trailing Z
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    def get_or_create_default(self):
        return self.get_or_create("default")

    def get_or_create(self, name: str):
        conn = self.db.connect()
        cur = conn.cursor()

        # Try find project
        cur.execute("SELECT id FROM projects WHERE name = ?", (name,))
        row = cur.fetchone()

        if row:
            conn.close()
            return name

        # Create project
        cur.execute(
            "INSERT INTO projects(name, created_at) VALUES (?, ?)",
            (name, self._now())
        )
        conn.commit()
        conn.close()
        return name

    def get_distilled_project(self, name: str):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT summary FROM distilled "
            "WHERE project_name = ? AND chat_id IS NULL "
            "ORDER BY created_at DESC LIMIT 1",
            (name,)
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else ""
