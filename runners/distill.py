#!/usr/bin/env python3
# distill.py - reads recent messages and creates a short distilled summary stored in `distilled`
import argparse, textwrap, datetime
from core.db.database import Database, init_db

def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"

def simple_distill(messages):
    # naive distillation: keep roles and sentences; return short summary
    # join user messages then assistant messages and produce a 200-char summary
    s = []
    for r in messages[-10:]:
        s.append(f"{r['role']}: {r['content']}")
    joined = "\n".join(s)
    # very simple compression: take first 400 chars
    return joined.strip()[:400]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--chat", required=True)
    args = parser.parse_args()

    init_db(args.db)
    db = Database(args.db)
    conn = db.connect()
    cur = conn.cursor()
    cur.execute("SELECT role, content, ts FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT 50", (args.chat,))
    rows = cur.fetchall()
    messages = list(reversed(rows))
    summary = simple_distill(messages)
    if summary:
        cur.execute("INSERT INTO distilled(project_name, chat_id, summary, created_at) VALUES (?,?,?,?)",
                    (args.project, args.chat, summary, now_iso()))
        conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
