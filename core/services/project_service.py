# core/services/project_service.py
from datetime import datetime, UTC
from core.db.database import Database


class ProjectService:
    def __init__(self, db: Database):
        self.db = db

    def _now(self):
        # timezone-aware UTC with trailing Z
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")

    # ---------------------------------------------------------
    # PROJECT CREATION
    # ---------------------------------------------------------
    def get_or_create_default(self):
        return self.get_or_create("default")

    def get_or_create(self, name: str):
        conn = self.db.connect()
        cur = conn.cursor()

        cur.execute("SELECT id FROM projects WHERE name=?", (name,))
        row = cur.fetchone()

        if row:
            conn.close()
            return name

        cur.execute(
            "INSERT INTO projects(name, created_at) VALUES (?, ?)",
            (name, self._now())
        )
        conn.commit()
        conn.close()
        return name

    # ---------------------------------------------------------
    # PROJECT-LEVEL DISTILLED SUMMARY
    # ---------------------------------------------------------
    def add_project_summary(self, project_name: str, text: str):
        """
        Insert a new distilled project summary.
        """
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO project_summaries(project_name, summary, created_at)
            VALUES (?,?,?)
            """,
            (project_name, text, self._now())
        )
        conn.commit()
        conn.close()

    def get_distilled_project(self, name: str) -> str:
        """
        Retrieve the latest distilled project-level summary.
        """
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT summary 
            FROM project_summaries
            WHERE project_name = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (name,)
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else ""
