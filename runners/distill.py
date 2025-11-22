#!/usr/bin/env python3
# distill.py — reads recent messages and stores a short distilled summary
import argparse
import datetime
from core.db.database import Database, init_db


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def simple_distill(messages):
    if not messages:
        return ""

    parts = []
    for msg in messages[-10:]:
        role = msg["role"]
        content = msg["content"].strip()
        parts.append(f"{role}: {content}")

    blob = "\n".join(parts).strip()
    return blob[:400]


def main():
    parser = argparse.ArgumentParser(description="Background chat distillation")
    parser.add_argument("--db", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--chat", required=True)
    args = parser.parse_args()

    init_db(args.db)
    db = Database(args.db)
    conn = db.connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT role, content, ts FROM messages "
        "WHERE chat_id = ? ORDER BY id DESC LIMIT 50",
        (args.chat,)
    )
    rows = cur.fetchall()
    messages = list(reversed(rows))

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
