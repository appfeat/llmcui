# cli/commands/banner.py

def show_status_banner(settings, db, project, chat_id):
    """
    Print the status banner if enabled.
    """

    if not settings.get_bool("show_status", False):
        return

    conn = db.connect()
    cur = conn.execute("SELECT title FROM chats WHERE id = ?", (chat_id,))
    row = cur.fetchone()
    conn.close()

    chat_title = row["title"] if row and row["title"] else "(untitled)"

    print(f"[project: {project} | {chat_title}]")
    print()
