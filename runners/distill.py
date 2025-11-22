#!/usr/bin/env python3
# runners/distill.py — background distillation for chat + project summaries using LLM
import argparse
import datetime
import sys

from core.db.database import Database, init_db
from core.services.project_service import ProjectService
from core.services.chat_service import ChatService
from core.services.message_service import MessageService
from core.services.llm_service import LLMService


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def main():
    parser = argparse.ArgumentParser(description="Background chat + project distillation (LLM-backed)")
    parser.add_argument("--db", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--chat", required=True)
    args = parser.parse_args()

    # Initialize
    init_db(args.db)
    db = Database(args.db)

    chat_svc = ChatService(db)
    project_svc = ProjectService(db)
    msg_svc = MessageService(db)
    llm = LLMService()  # uses default llm binary; override if you want

    # 1) Fetch recent chat messages
    try:
        recent_msgs = msg_svc.last_messages(args.chat, limit=50)
    except Exception as e:
        print(f"[distill] failed to load recent messages for chat {args.chat}: {e}", file=sys.stderr)
        recent_msgs = []

    # 2) Fetch project messages (for project-level summary)
    try:
        conn = db.connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT m.role, m.content, m.ts
            FROM messages m
            JOIN chats c ON m.chat_id = c.id
            JOIN projects p ON c.project_id = p.id
            WHERE p.name = ?
            ORDER BY m.id ASC
            """,
            (args.project,)
        )
        project_rows = cur.fetchall()
        conn.close()
    except Exception as e:
        print(f"[distill] failed to load project messages for project {args.project}: {e}", file=sys.stderr)
        project_rows = []

    # Convert rows to list-like mapping where possible (sqlite3.Row supports mapping access)
    chat_msgs = list(recent_msgs)
    project_msgs = list(project_rows)

    # 3) Use single LLM call to request structured JSON (chat + project).
    try:
        chat_summary, project_summary = llm.summarize_both(chat_msgs, project_msgs)
    except Exception as e:
        print(f"[distill] llm.summarize_both failed: {e}", file=sys.stderr)
        chat_summary, project_summary = "", ""

    # 4) Persist chat-level summary (distilled)
    try:
        if chat_summary:
            conn = db.connect()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO distilled(project_name, chat_id, summary, created_at)
                VALUES (?,?,?,?)
                """,
                (args.project, args.chat, chat_summary, now_iso())
            )
            conn.commit()
            conn.close()
            print(f"[distill] wrote chat summary for chat={args.chat} (len={len(chat_summary)})")
    except Exception as e:
        print(f"[distill] failed to write chat distilled row: {e}", file=sys.stderr)

    # 5) Persist project-level summary (project_summaries table)
    try:
        if project_summary:
            latest = project_svc.get_distilled_project(args.project) or ""
            if project_summary.strip() != latest.strip():
                project_svc.add_project_summary(args.project, project_summary)
                print(f"[distill] wrote project summary for project={args.project} (len={len(project_summary)})")
            else:
                print(f"[distill] project summary unchanged for project={args.project} — skipping write")
    except Exception as e:
        print(f"[distill] failed to write project summary: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
