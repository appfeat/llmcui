#!/usr/bin/env python3
# distill.py — reads recent messages and stores a short distilled summary
import argparse
import datetime
import textwrap

from core.db.database import Database, init_db


def now_iso():
    """UTC timestamp in ISO format."""
    return datetime.datetime.utcnow().isoformat() + "Z"


def simple_distill(messages):
    """
    Very simple distiller:
    - Uses last 10 messages (user + assistant)
    - Creates a compact 400-character slice
    """
    if not messages:
        return ""

    parts = []
    for msg in messages[-10:]:
        role = msg.get("role", "?")
        content = msg.get("content", "").strip()
        parts.append(f"{role}: {content}")

    blob = "\n".join(parts).strip()
    return blob[:400]  # cap for safety


def main():
    parser = argparse.ArgumentParser(description="Background chat distillation")
    parser.add_argument("--db", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--chat", required=True)
    args = parser.parse_args()

    # Initialize DB
    init_db(args.db)
    db = Database(args.db)
    conn = db.connect()
    cur = conn.cursor()

    # Load last 50 messages
    cur.execute(
        "SELECT role, content, ts FROM messages "
        "WHERE chat_id = ? ORDER BY id DESC LIMIT 50",
        (args.chat,)
    )
    rows = cur.fetchall()
    messages = list(reversed(rows))  # chronological order

    # Distill
    summary = simple_distill(messages)

    if summary:
        cur.execute(
            """
            INSERT INTO distilled(project_name, chat_id, summary, created_at)
            VALUES (?,?,?,?)
            """,
            (args.project, args.chat, summary, now_iso())
        )
        conn.commit()

    conn.close()


if __name__ == "__main__":
    main()
