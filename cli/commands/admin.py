# cli/commands/admin.py

import time
import uuid
from core.db.database import Database


def _create_chat_sql(db: Database, project_name: str) -> str:
    """Direct SQL fallback chat creation."""
    conn = db.connect()
    cur = conn.cursor()

    cur.execute("SELECT id FROM projects WHERE name = ?", (project_name,))
    p = cur.fetchone()

    if not p:
        conn.close()
        raise ValueError(f"Project not found: {project_name}")

    project_id = p["id"]
    chat_id = "chat-" + uuid.uuid4().hex[:8]
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    cur.execute(
        "INSERT INTO chats(id, project_id, title, created_at, last_used) "
        "VALUES (?, ?, ?, ?, ?)",
        (chat_id, project_id, "(untitled)", now, now)
    )

    conn.commit()
    conn.close()
    return chat_id


def handle_admin_commands(args, db, project_svc, chat_svc) -> bool:
    """
    Executes admin commands and returns True if command was handled.
    False → main logic continues.
    """

    # ------------------------------
    # LIST PROJECTS
    # ------------------------------
    if args.list_projects:
        conn = db.connect()
        rows = conn.execute(
            "SELECT id, name, created_at FROM projects ORDER BY id"
        ).fetchall()
        conn.close()

        if not rows:
            print("No projects found.")
        else:
            print("Projects:")
            for r in rows:
                print(f"- {r['name']} (created: {r['created_at']})")

        return True

    # ------------------------------
    # LIST CHATS
    # ------------------------------
    if args.list_chats:
        project = args.project or project_svc.get_or_create_default()

        conn = db.connect()
        rows = conn.execute(
            "SELECT id, title, created_at, last_used FROM chats "
            "WHERE project_id = (SELECT id FROM projects WHERE name = ?) "
            "ORDER BY last_used DESC",
            (project,)
        ).fetchall()
        conn.close()

        if not rows:
            print(f"No chats found for project '{project}'.")
        else:
            print(f"Chats for project '{project}':")
            for r in rows:
                title = r["title"] if r["title"] else "(untitled)"
                print(
                    f"- {r['id']} | {title} | last used: {r['last_used']}"
                )

        return True

    # ------------------------------
    # CREATE PROJECT
    # ------------------------------
    if args.new_project:
        name = args.new_project.strip()

        if not name:
            print("Invalid project name.")
            return True

        conn = db.connect()
        try:
            conn.execute(
                "INSERT INTO projects(name, created_at) "
                "VALUES (?, datetime('now'))",
                (name,)
            )
            conn.commit()
            print(f"Created project '{name}'.")
        except Exception:
            print(f"Project '{name}' already exists or cannot be created.")
        finally:
            conn.close()

        return True

    # ------------------------------
    # CREATE CHAT
    # ------------------------------
    if args.new_chat:
        project = args.project or project_svc.get_or_create_default()

        try:
            if hasattr(chat_svc, "force_new_chat"):
                new_chat_id = chat_svc.force_new_chat(project)
            else:
                new_chat_id = _create_chat_sql(db, project)

            print(f"Created new chat: {new_chat_id}")

        except Exception as e:
            print("Failed to create chat:", e)

        return True

    # No admin command matched → continue main
    return False
