import os
import cli.interactive.menu as M


def post_response_menu(
    db,
    project_svc,
    chat_svc,
    msg_svc,
    llm,
    settings,
    current_project,
    current_chat,
):
    """
    Menu shown AFTER an LLM response.
    """

    while True:
        print("\nActions:")
        print("  a → Ask another question")
        print("  f → Pipe a file + ask")
        print("  c → Switch chat")
        print("  p → Switch project & chat")
        print("  x → Exit")

        choice = M.ask("\nChoose: ").lower()

        # EXIT
        if choice == "x":
            return 0

        # ASK ANOTHER QUESTION
        if choice == "a":
            prompt = M.ask("Your message: ")
            return rerun_llm(
                current_project,
                current_chat,
                prompt,
            )

        # PIPE A FILE + QUESTION
        if choice == "f":
            path = M.ask("File path: ").strip()
            if not os.path.isfile(path):
                print("Invalid file path.")
                continue

            with open(path, "r", errors="ignore") as fh:
                content = fh.read()

            question = M.ask("Your question about this file: ")
            combined = f"### FILE: {path}\n{content}\n\n{question}"

            return rerun_llm(
                current_project,
                current_chat,
                combined,
            )

        # SWITCH CHAT
        if choice == "c":
            chat = M.select_chat(db, chat_svc, current_project)
            if chat:
                M.show_chat_history(msg_svc, chat)
                prompt = M.ask("Your message: ")
                return rerun_llm(
                    current_project,
                    chat,
                    prompt,
                )
            continue

        # SWITCH PROJECT + CHAT
        if choice == "p":
            proj = M.select_project(db, project_svc)
            if proj:
                chat = M.select_chat(db, chat_svc, proj)
                if chat:
                    M.show_chat_history(msg_svc, chat)
                    prompt = M.ask("Your message: ")
                    return rerun_llm(
                        proj,
                        chat,
                        prompt,
                    )
            continue

        print("Invalid choice.")


def rerun_llm(project, chat_id, prompt):
    """
    Returns a dict understood by main.py for re-running the LLM.
    """
    return {
        "interactive_project": project,
        "interactive_chat": chat_id,
        "interactive_prompt": prompt,
    }
