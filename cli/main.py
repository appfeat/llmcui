#!/usr/bin/env python3
import argparse
import os
import subprocess
import time

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
    """
    If show_status has never been set (first run), default to ON.
    """
    if settings.get("show_status") is None:
        settings.set("show_status", "true")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ai",
        description="llmcui MVP wrapper for llm"
    )
    parser.add_argument("-p", "--project", help="project name (use default if omitted)")
    parser.add_argument("-c", "--chat", help="chat id")
    parser.add_argument("-r", "--reset", action="store_true", help="reset chat history")
    parser.add_argument("-f", "--filemode", action="store_true", help="file selection mode")
    parser.add_argument("--toggle-status", action="store_true",
                        help="toggle project/chat header display")
    parser.add_argument("prompt", nargs="?", help="prompt text")
    parser.add_argument("selector", nargs="?", help="file selector (e.g. 0,1 or 0-2)")
    args = parser.parse_args(argv)

    # --------------------------------------------
    # Toggle status header only
    # --------------------------------------------
    if args.toggle_status:
        init_db(DB_PATH)
        db = Database(DB_PATH)
        settings = SettingsService(db)
        new_val = settings.toggle("show_status", default=False)
        print(f"Status header now {'ON' if new_val else 'OFF'}")
        return 0

    # No prompt → help
    if not args.prompt:
        parser.print_usage()
        return 1

    # --------------------------------------------
    # Initialize DB + services
    # --------------------------------------------
    init_db(DB_PATH)
    db = Database(DB_PATH)

    project_svc = ProjectService(db)
    chat_svc = ChatService(db)
    msg_svc = MessageService(db)
    llm = LLMService()
    settings = SettingsService(db)

    ensure_first_run_status_on(settings)

    # --------------------------------------------
    # Resolve project + chat
    # --------------------------------------------
    project = args.project or project_svc.get_or_create_default()
    chat_id = args.chat or chat_svc.get_or_create_first(project)

    # Reset chat
    if args.reset:
        chat_svc.reset_chat(chat_id)

    # --------------------------------------------
    # New-chat title generation
    # --------------------------------------------
    if chat_svc.is_new_chat(chat_id):
        title = llm.generate_title(args.prompt)
        if title:
            chat_svc.update_title(chat_id, title)

    # --------------------------------------------
    # Context summaries
    # --------------------------------------------
    project_summary = project_svc.get_distilled_project(project)
    chat_summary = chat_svc.get_distilled_chat(chat_id)

    prompt_parts = []
    if project_summary:
        prompt_parts.append(f"[PROJECT_CONTEXT]\n{project_summary}\n")
    if chat_summary:
        prompt_parts.append(f"[CHAT_CONTEXT]\n{chat_summary}\n")

    prompt_parts.append("### CURRENT_USER_MESSAGE")
    prompt_parts.append(args.prompt)

    # --------------------------------------------
    # File selection mode
    # --------------------------------------------
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

    # --------------------------------------------
    # Save user message
    # --------------------------------------------
    msg_svc.add_message(chat_id, "user", args.prompt)

    # --------------------------------------------
    # Status banner (with readable chat title)
    # --------------------------------------------
    if settings.get_bool("show_status", False):
        conn = db.connect()
        cur = conn.execute("SELECT title FROM chats WHERE id = ?", (chat_id,))
        row = cur.fetchone()
        conn.close()

        chat_title = row["title"] if row and row["title"] else "(untitled)"
        print(f"[project: {project} | {chat_title}]")
        print()

    # --------------------------------------------
    # LLM call
    # --------------------------------------------
    start = time.time()
    response_text = llm.call_prompt(full_prompt)
    duration = time.time() - start

    if response_text is None:
        print("LLM call failed.")
        return 1

    print(response_text)
    print()
    print(f"⏱️ Runtime (model call): {duration:.2f}s")

    # --------------------------------------------
    # Store assistant message
    # --------------------------------------------
    msg_svc.add_message(chat_id, "assistant", response_text)
    chat_svc.append_archive(chat_id, args.prompt, response_text)

    # --------------------------------------------
    # Background distillation
    # --------------------------------------------
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
