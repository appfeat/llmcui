# cli/interactive/menu.py
import os
import time

from core.services.project_service import ProjectService
from core.services.chat_service import ChatService
from core.services.message_service import MessageService


# -----------------------------------------------------------
# Utility: safe input wrapper
# -----------------------------------------------------------
def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("")
        return ""


# -----------------------------------------------------------
# PROJECT SELECTION
# -----------------------------------------------------------
def select_project(db, project_svc: ProjectService) -> str:
    conn = db.connect()
    rows = conn.execute(
        "SELECT name, created_at FROM projects ORDER BY name"
    ).fetchall()
    conn.close()

    print("\n=== Projects ===")
    if not rows:
        print("No projects found. Creating default.")
        return project_svc.get_or_create_default()

    for i, r in enumerate(rows):
        print(f"{i}. {r['name']}   (created {r['created_at']})")

    print("n. Create new project")
    print("x. Cancel")

    while True:
        sel = ask("\nSelect project: ").lower()

        if sel == "x":
            return None

        if sel == "n":
            name = ask("New project name: ").strip()
            if name:
                return project_svc.get_or_create(name)
            print("Invalid name.")
            continue

        if sel.isdigit():
            idx = int(sel)
            if 0 <= idx < len(rows):
                return rows[idx]["name"]

        print("Invalid choice.")


# -----------------------------------------------------------
# CHAT SELECTION
# -----------------------------------------------------------
def select_chat(db, chat_svc: ChatService, project: str) -> str:
    conn = db.connect()
    rows = conn.execute(
        """
        SELECT chats.id, chats.title, chats.last_used
        FROM chats
        JOIN projects ON chats.project_id = projects.id
        WHERE projects.name = ?
        ORDER BY chats.last_used DESC
        """,
        (project,),
    ).fetchall()
    conn.close()

    print(f"\n=== Chats in '{project}' ===")

    if not rows:
        print("No chats found. Creating first chat.")
        return chat_svc.force_new_chat(project)

    for i, r in enumerate(rows):
        title = r["title"] or "(untitled)"
        print(f"{i}. {title}   [{r['id']}]   last used: {r['last_used']}")

    print("n. Create new chat")
    print("x. Cancel")

    while True:
        sel = ask("\nSelect chat: ").lower()

        if sel == "x":
            return None

        if sel == "n":
            return chat_svc.force_new_chat(project)

        if sel.isdigit():
            idx = int(sel)
            if 0 <= idx < len(rows):
                return rows[idx]["id"]

        print("Invalid choice.")


# -----------------------------------------------------------
# VIEW FULL CHAT HISTORY
# -----------------------------------------------------------
def show_chat_history(msg_svc: MessageService, chat_id: str):
    print("\n=== Chat History ===")
    rows = msg_svc.get_messages(chat_id)

    if not rows:
        print("(empty)")
        return

    for r in rows:
        role = "You" if r["role"] == "user" else "AI"
        ts = r["ts"]
        content = r["content"]
        print(f"\n[{role} @ {ts}]")
        print(content)
        print("-" * 40)


# -----------------------------------------------------------
# MAIN INTERACTIVE ENTRY
# -----------------------------------------------------------
def interactive_entry(db, project_svc, chat_svc, msg_svc, llm, settings):
    print("========================================")
    print("         llmcui interactive mode        ")
    print("========================================")
    print("Actions:")
    print("  0 → Start a new project")
    print("  1 → Browse existing projects")
    print("  2 → Use default project")
    print("  x → Exit")
    print("========================================")

    while True:
        choice = ask("Choose option: ").lower()

        # Exit
        if choice == "x":
            return 0

        # ----------------------------------------
        # CREATE NEW PROJECT
        # ----------------------------------------
        if choice == "0":
            name = ask("Enter new project name: ").strip()
            if not name:
                print("Invalid name.")
                continue

            project = project_svc.get_or_create(name)
            chat_id = chat_svc.force_new_chat(project)
            prompt = ask("Enter prompt: ")

            return _return_interactive_choice(project, chat_id, prompt)

        # ----------------------------------------
        # BROWSE PROJECTS
        # ----------------------------------------
        if choice == "1":
            project = select_project(db, project_svc)
            if not project:
                continue

            chat = select_chat(db, chat_svc, project)
            if not chat:
                continue

            show_chat_history(msg_svc, chat)

            print("\nOptions:")
            print("  c → Continue this chat")
            print("  p → Pick a different project")
            print("  x → Exit")

            while True:
                inner = ask("\nChoose: ").lower()

                if inner == "x":
                    return 0
                if inner == "p":
                    break       # go back to main menu
                if inner == "c":
                    prompt = ask("Your message: ")
                    return _return_interactive_choice(project, chat, prompt)

                print("Invalid choice.")

        # ----------------------------------------
        # DEFAULT PROJECT
        # ----------------------------------------
        if choice == "2":
            project = project_svc.get_or_create_default()
            chat = chat_svc.get_or_create_first(project)

            show_chat_history(msg_svc, chat)
            prompt = ask("Your message: ")

            return _return_interactive_choice(project, chat, prompt)

        print("Invalid choice. Try again.")


# -----------------------------------------------------------
# Return interactive choice back to main.py
# -----------------------------------------------------------
def _return_interactive_choice(project: str, chat_id: str, prompt: str):
    return {
        "interactive_project": project,
        "interactive_chat": chat_id,
        "interactive_prompt": prompt
    }
