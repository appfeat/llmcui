#!/usr/bin/env python3
import argparse
import os
import subprocess
import time
import uuid

from core.db.database import Database, init_db
from core.services.project_service import ProjectService
from core.services.chat_service import ChatService
from core.services.message_service import MessageService
from core.services.llm_service import LLMService
from core.services.settings_service import SettingsService

ROOT = os.path.expanduser("~/.llmcui")
os.makedirs(ROOT, exist_ok=True)
os.environ.setdefault("LLMCUI_ROOT", ROOT)
DB_PATH = os.path.join(ROOT, "ai.db")


def ensure_first_run_status_on(settings: SettingsService):
    """If show_status has never been set (first run), default to ON."""
    if settings.get("show_status") is None:
        settings.set("show_status", "true")


def _force_create_chat_via_sql(db: Database, project_name: str) -> str:
    """
    Create a new chat for project_name using direct SQL.
    Returns the new chat id or raises on missing project.
    """
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
        "INSERT INTO chats(id, project_id, title, created_at, last_used) VALUES (?, ?, ?, ?, ?)",
        (chat_id, project_id, "(untitled)", now, now),
    )
    conn.commit()
    conn.close()
    return chat_id


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ai",
        description="llmcui MVP wrapper for llm"
    )

    # ------------------------------------------------------------
    # EXISTING ARGUMENTS
    # ------------------------------------------------------------
    parser.add_argument("-p", "--project", help="project name (use default if omitted)")
    parser.add_argument("-c", "--chat", help="chat id")
    parser.add_argument("-r", "--reset", action="store_true", help="reset chat history")
    parser.add_argument("-f", "--filemode", action="store_true", help="file selection mode")
    parser.add_argument("--toggle-status", action="store_true",
                        help="toggle project/chat header display")

    # ------------------------------------------------------------
    # NEW ADMIN / MAINTENANCE COMMANDS
    # ------------------------------------------------------------
    parser.add_argument("--list-projects", action="store_true",
                        help="List all existing projects")
    parser.add_argument("--list-chats", action="store_true",
                        help="List all chats for a project")
    parser.add_argument("--new-project", help="Create a new project by name")
    parser.add_argument("--new-chat", action="store_true",
                        help="Create a new chat in the selected or default project")

    # Positional arguments (unchanged)
    parser.add_argument("prompt", nargs="?", help="prompt text")
    parser.add_argument("selector", nargs="?", help="file selector (e.g. 0,1 or 0-2)")

    args = parser.parse_args(argv)

    # Toggle header flag
    if args.toggle_status:
        init_db(DB_PATH)
        db = Database(DB_PATH)
        settings = SettingsService(db)
        new_val = settings.toggle("show_status", default=False)
        print(f"Status header now {'ON' if new_val else 'OFF'}")
        return 0

    # If user asked for administrative actions but didn't supply prompt, allow admin flows:
    # (we initialize DB and services early so admin flags work)
    init_db(DB_PATH)
    db = Database(DB_PATH)
    project_svc = ProjectService(db)
    chat_svc = ChatService(db)
    msg_svc = MessageService(db)
    llm = LLMService()
    settings = SettingsService(db)

    # Ensure show_status default on first run
    ensure_first_run_status_on(settings)

    # -----------------------------
    # Administrative command handling
    # -----------------------------
    if args.list_projects:
        conn = db.connect()
        rows = conn.execute("SELECT id, name, created_at FROM projects ORDER BY id").fetchall()
        conn.close()
        if not rows:
            print("No projects found.")
        else:
            print("Projects:")
            for r in rows:
                print(f"- {r['name']}  (created: {r['created_at']})")
        return 0

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
                title = r['title'] if r['title'] else "(untitled)"
                print(f"- {r['id']} | {title} | last used: {r['last_used']}")
        return 0

    if args.new_project:
        name = args.new_project.strip()
        if not name:
            print("Invalid project name.")
            return 1
        conn = db.connect()
        try:
            conn.execute(
                "INSERT INTO projects(name, created_at) VALUES (?, datetime('now'))",
                (name,)
            )
            conn.commit()
            print(f"Created project '{name}'.")
        except Exception:
            print(f"Project '{name}' already exists or could not be created.")
        finally:
            conn.close()
        return 0

    if args.new_chat:
        project = args.project or project_svc.get_or_create_default()
        # prefer ChatService helper if present
        try:
            if hasattr(chat_svc, "force_new_chat"):
                new_chat_id = chat_svc.force_new_chat(project)
            elif hasattr(chat_svc, "force_create_new_chat"):
                new_chat_id = chat_svc.force_create_new_chat(project)
            else:
                new_chat_id = _force_create_chat_via_sql(db, project)
            print(f"Created new chat: {new_chat_id}")
            return 0
        except Exception as e:
            print("Failed to create new chat:", e)
            return 1

    # From here on we require a prompt to run the normal flow
    if not args.prompt:
        parser.print_usage()
        return 1

    # --------------------------------------------
    # Resolve project + chat for normal usage
    # --------------------------------------------
    project = args.project or project_svc.get_or_create_default()
    chat_id = args.chat or chat_svc.get_or_create_first(project)

    # Reset chat content but keep metadata
    if args.reset:
        chat_svc.reset_chat(chat_id)

    # New-chat → generate title (only for truly empty chats)
    if chat_svc.is_new_chat(chat_id):
        title = llm.generate_title(args.prompt)
        if title:
            chat_svc.update_title(chat_id, title)

    # Summaries
    project_summary = project_svc.get_distilled_project(project)
    chat_summary = chat_svc.get_distilled_chat(chat_id)

    prompt_parts = []
    if project_summary:
        prompt_parts.append(f"[PROJECT_CONTEXT]\n{project_summary}\n")
    if chat_summary:
        prompt_parts.append(f"[CHAT_CONTEXT]\n{chat_summary}\n")

    # Main user message
    prompt_parts.append("### CURRENT_USER_MESSAGE")
    prompt_parts.append(args.prompt)

    # Brevity rules (short by default, full for code)
    prompt_parts.append("""
### STYLE_GUIDE
- Keep responses short, precise, and compact by default.
- Expand fully only when producing code, configuration files, or command sequences.
- When producing code, return the complete working code without omissions.
- For non-code answers: avoid long paragraphs or repeated explanations.
""")

    # File selection
    if args.filemode and args.selector:
        try:
            sel = args.selector
            if "-" in sel:
                a, b = sel.split("-", 1)
                files = range(int(a), int(b) + 1)
            else:
                files = [int(x) for x in sel.split(",")]

            cwd_files = [f for f in os.listdir(".") if os.path.isfile(f)]

            for idx in files:
                if 0 <= idx < len(cwd_files):
                    fname = cwd_files[idx]
                    with open(fname, "r", errors="ignore") as fh:
                        prompt_parts.append(f"### FILE: {fname}\n{fh.read()}\n")

        except Exception as ex:
            print("file selection parse error:", ex)

    full_prompt = "\n\n".join(prompt_parts)

    # Save user message
    msg_svc.add_message(chat_id, "user", args.prompt)

    # Status banner (readable title)
    if settings.get_bool("show_status", False):
        conn = db.connect()
        cur = conn.execute("SELECT title FROM chats WHERE id = ?", (chat_id,))
        row = cur.fetchone()
        conn.close()

        chat_title = row["title"] if row and row["title"] else "(untitled)"
        print(f"[project: {project} | {chat_title}]")
        print()

    # LLM call
    start = time.time()
    response_text = llm.call_prompt(full_prompt)
    duration = time.time() - start

    if response_text is None:
        print("LLM call failed.")
        return 1

    print(response_text)
    print()
    print(f"⏱️ Runtime (model call): {duration:.2f}s")

    # Store assistant message
    msg_svc.add_message(chat_id, "assistant", response_text)
    chat_svc.append_archive(chat_id, args.prompt, response_text)

    # Background distillation (async)
    try:
        distill_path = os.path.join(
            os.path.dirname(__file__), "..", "runners", "distill.py"
        )
        subprocess.Popen(
            [
                "python3",
                distill_path,
                "--db",
                DB_PATH,
                "--project",
                project,
                "--chat",
                chat_id,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    main()
