# cli/commands/prompt_builder.py

import os


def build_prompt(args, db, project, chat_id, project_svc, chat_svc):
    """
    Build the full LLM prompt, cleanly separated from main.
    """

    project_summary = project_svc.get_distilled_project(project)
    chat_summary = chat_svc.get_distilled_chat(chat_id)

    parts = []

    # -----------------------------
    # PROJECT SUMMARY
    # -----------------------------
    if project_summary:
        parts.append(f"[PROJECT_CONTEXT]\n{project_summary}\n")

    # -----------------------------
    # CHAT SUMMARY
    # -----------------------------
    if chat_summary:
        parts.append(f"[CHAT_CONTEXT]\n{chat_summary}\n")

    # -----------------------------
    # MAIN USER MESSAGE
    # -----------------------------
    parts.append("### CURRENT_USER_MESSAGE")
    parts.append(args.prompt)

    # -----------------------------
    # BREVITY RULES
    # -----------------------------
    parts.append(
        """
### STYLE_GUIDE
- Keep responses short, precise, and compact.
- Expand fully only for code, configs, or command sequences.
- When writing code, output complete runnable code.
- Avoid long explanations; stay concise.
"""
    )

    # -----------------------------
    # FILE SELECTION MODE
    # -----------------------------
    if args.filemode and args.selector:
        try:
            sel = args.selector

            if "-" in sel:
                a, b = sel.split("-", 1)
                files = range(int(a), int(b) + 1)
            else:
                files = [int(x) for x in sel.split(",")]

            cwd_files = [
                f for f in os.listdir(".")
                if os.path.isfile(f)
            ]

            for idx in files:
                if 0 <= idx < len(cwd_files):
                    fname = cwd_files[idx]
                    with open(fname, "r", errors="ignore") as fh:
                        parts.append(f"### FILE: {fname}\n{fh.read()}\n")

        except Exception as ex:
            parts.append(f"[FILE_SELECTION_ERROR] {ex}")

    return "\n\n".join(parts)
