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

from cli.commands.admin import handle_admin_commands
from cli.commands.prompt_builder import build_prompt
from cli.commands.banner import show_status_banner
from cli.interactive.menu import interactive_entry
from cli.interactive.post_response import post_response_menu


ROOT = os.path.expanduser("~/.llmcui")
os.makedirs(ROOT, exist_ok=True)
os.environ.setdefault("LLMCUI_ROOT", ROOT)

DB_PATH = os.path.join(ROOT, "ai.db")


def ensure_first_run_status_on(settings: SettingsService):
    """Enable show_status=ON for first-time users."""
    if settings.get("show_status") is None:
        settings.set("show_status", "true")


def running_under_pytest() -> bool:
    """Detect pytest to avoid background Popen warnings & interactive menus."""
    return "PYTEST_CURRENT_TEST" in os.environ


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ai",
        description="llmcui MVP wrapper for llm"
    )

    # NORMAL USER FLAGS
    parser.add_argument("-p", "--project", help="project name")
    parser.add_argument("-c", "--chat", help="chat id")
    parser.add_argument("-r", "--reset", action="store_true", help="reset chat")
    parser.add_argument("-f", "--filemode", action="store_true", help="file mode")
    parser.add_argument("--toggle-status", action="store_true", help="toggle banner")

    # ADMIN FLAGS
    parser.add_argument("--list-projects", action="store_true")
    parser.add_argument("--list-chats", action="store_true")
    parser.add_argument("--new-project")
    parser.add_argument("--new-chat", action="store_true")

    # FREE PROMPT
    parser.add_argument("prompt", nargs="?", help="prompt")
    parser.add_argument("selector", nargs="?", help="file selector")

    args = parser.parse_args(argv)

    # INIT SERVICES
    init_db(DB_PATH)
    db = Database(DB_PATH)

    project_svc = ProjectService(db)
    chat_svc = ChatService(db)
    msg_svc = MessageService(db)
    llm = LLMService()
    settings = SettingsService(db)

    ensure_first_run_status_on(settings)

    # ADMIN COMMANDS
    if handle_admin_commands(args, db, project_svc, chat_svc):
        return 0

    # INTERACTIVE MODE
    if (
        not args.prompt
        and not args.list_projects
        and not args.list_chats
        and not args.new_project
        and not args.new_chat
        and not args.toggle_status
    ):
        inter = interactive_entry(
            db, project_svc, chat_svc, msg_svc, llm, settings
        )

        if isinstance(inter, dict):
            args.project = inter["interactive_project"]
            args.chat = inter["interactive_chat"]
            args.prompt = inter["interactive_prompt"]
        else:
            return inter

    # PROMPT REQUIRED
    if not args.prompt:
        parser.print_usage()
        return 1

    # RESOLVE PROJECT + CHAT
    project = args.project or project_svc.get_or_create_default()
    chat_id = args.chat or chat_svc.get_or_create_first(project)

    if args.reset:
        chat_svc.reset_chat(chat_id)

    # TITLE GENERATION FOR NEW CHAT
    if chat_svc.is_new_chat(chat_id):
        title = llm.generate_title(args.prompt)
        if title:
            chat_svc.update_title(chat_id, title)

    # BUILD PROMPT
    full_prompt = build_prompt(
        args=args,
        db=db,
        project=project,
        chat_id=chat_id,
        project_svc=project_svc,
        chat_svc=chat_svc
    )

    # SAVE USER MESSAGE
    msg_svc.add_message(chat_id, "user", args.prompt)

    # SHOW BANNER
    show_status_banner(settings, db, project, chat_id)

    # LLM CALL
    start = time.time()
    response_text = llm.call_prompt(full_prompt)
    duration = time.time() - start

    if response_text is None:
        print("LLM call failed.")
        return 1

    print(response_text)
    print()
    print(f"⏱️ Runtime (model call): {duration:.2f}s")

    # SAVE ASSISTANT MESSAGE
    msg_svc.add_message(chat_id, "assistant", response_text)
    chat_svc.append_archive(chat_id, args.prompt, response_text)

    # BACKGROUND DISTILLATION SKIPPED DURING TESTS
    if not running_under_pytest():
        try:
            distill_path = os.path.join(
                os.path.dirname(__file__), "..", "runners", "distill.py"
            )
            subprocess.Popen(
                [
                    "python3", distill_path,
                    "--db", DB_PATH,
                    "--project", project,
                    "--chat", chat_id,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

    # POST-RESPONSE MENU DISABLED UNDER PYTEST
    if running_under_pytest():
        return 0

    # POST-RESPONSE MENU LOOP
    return post_response_menu(
        db, project_svc, chat_svc, msg_svc, llm, settings,
        current_project=project,
        current_chat=chat_id
    )


if __name__ == "__main__":
    main()
