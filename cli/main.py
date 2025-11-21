# cli/main.py
import argparse
import os
import subprocess
import time

from core.db.database import Database, init_db
from core.services.project_service import ProjectService
from core.services.chat_service import ChatService
from core.services.message_service import MessageService
from core.services.llm_service import LLMService

ROOT = os.path.expanduser("~/.llmcui")  # runtime folder
os.makedirs(ROOT, exist_ok=True)
os.environ.setdefault("LLMCUI_ROOT", ROOT)
DB_PATH = os.path.join(ROOT, "ai.db")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="ai",
        description="llmcui MVP wrapper for llm"
    )
    parser.add_argument("-p", "--project", help="project name (use default to skip prompt)")
    parser.add_argument("-c", "--chat", help="chat id")
    parser.add_argument("-r", "--reset", action="store_true", help="reset chat history")
    parser.add_argument("-f", "--filemode", action="store_true", help="file selection mode")
    parser.add_argument("prompt", nargs="?", help="prompt text")
    parser.add_argument("selector", nargs="?", help="file selector (e.g. 0,1 or 0-2)")
    args = parser.parse_args(argv)

    if not args.prompt:
        parser.print_usage()
        return 1

    # init DB
    init_db(DB_PATH)
    db = Database(DB_PATH)
    project_svc = ProjectService(db)
    chat_svc = ChatService(db)
    msg_svc = MessageService(db)
    llm = LLMService()

    # choose project
    project = args.project or project_svc.get_or_create_default()
    chat_id = args.chat or chat_svc.get_or_create_first(project)

    if args.reset:
        chat_svc.reset_chat(chat_id)

    # summaries
    project_summary = project_svc.get_distilled_project(project)
    chat_summary = chat_svc.get_distilled_chat(chat_id)

    prompt_parts = []
    if project_summary:
        prompt_parts.append(f"[PROJECT_CONTEXT]\n{project_summary}\n")
    if chat_summary:
        prompt_parts.append(f"[CHAT_CONTEXT]\n{chat_summary}\n")
    prompt_parts.append("### CURRENT_USER_MESSAGE")
    prompt_parts.append(args.prompt)

    # optional file selection
    if args.filemode and args.selector:
        try:
            sel = args.selector
            files = []

            if "-" in sel:
                s, e = sel.split("-", 1)
                files = list(range(int(s), int(e) + 1))
            else:
                files = [int(x) for x in sel.split(",")]

            cwd_files = [f for f in os.listdir(".") if os.path.isfile(f)]

            for i in files:
                if 0 <= i < len(cwd_files):
                    with open(cwd_files[i], "r", errors="ignore") as fh:
                        prompt_parts.append(f"### FILE: {cwd_files[i]}\n{fh.read()}\n")

        except Exception as ex:
            print("file selection parse error:", ex)

    full_prompt = "\n\n".join(prompt_parts)

    # save + llm call
    msg_svc.add_message(chat_id, "user", args.prompt)

    start = time.time()
    response_text = llm.call_prompt(full_prompt)
    duration = time.time() - start

    if response_text is None:
        print("LLM call failed.")
        return 1

    print(response_text)
    print()
    print(f"⏱️ Runtime (model call): {duration:.2f}s")

    # persist
    msg_svc.add_message(chat_id, "assistant", response_text)
    chat_svc.append_archive(chat_id, args.prompt, response_text)

    # background distillation
    try:
       # distill_path = os.path.join(os.path.dirname(__file__), "..", "distill.py")
        distill_path = os.path.join(os.path.dirname(__file__), "..", "runners", "distill.py")
        subprocess.Popen(
            ["python3", distill_path, "--db", DB_PATH, "--project", project, "--chat", chat_id],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

    return 0
