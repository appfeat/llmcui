import builtins
import pytest

from cli.interactive.menu import (
    select_project,
    select_chat,
    show_chat_history,
    interactive_entry,
)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
class FakeDB:
    """Small stub replicating .connect() returning rows."""
    def __init__(self, projects=None, chats=None):
        self.projects = projects or []
        self.chats = chats or []

    def connect(self):
        return FakeConn(self.projects, self.chats)


class FakeConn:
    def __init__(self, projects, chats):
        self._projects = projects
        self._chats = chats

    def execute(self, sql, args=None):
        sql = sql.lower()

        # SELECT FROM PROJECTS
        if "from projects" in sql:
            return FakeCursor(self._projects)

        # SELECT FROM CHATS JOIN PROJECTS
        if "from chats" in sql:
            pname = args[0]
            found = [c for c in self._chats if c["project"] == pname]
            return FakeCursor(found)

        return FakeCursor([])

    def fetchall(self):
        return []

    def close(self):
        pass


class FakeCursor:
    def __init__(self, items):
        self.items = items

    def fetchall(self):
        return self.items

    def fetchone(self):
        return self.items[0] if self.items else None


class FakeProjectService:
    def __init__(self):
        self.created = []

    def get_or_create_default(self):
        return "default"

    def get_or_create(self, name):
        self.created.append(name)
        return name


class FakeChatService:
    def __init__(self):
        self.created = {}

    def force_new_chat(self, project):
        cid = f"chat-{project}-new"
        self.created[project] = cid
        return cid


class FakeMsgService:
    def __init__(self, messages=None):
        self.messages = messages or []

    def get_messages(self, chat_id):
        return self.messages


# -------------------------------------------------------------------
# TEST select_project()
# -------------------------------------------------------------------
def test_select_project_choose_existing(monkeypatch):
    db = FakeDB(projects=[
        {"name": "proj1", "created_at": "T1"},
        {"name": "proj2", "created_at": "T2"},
    ])
    proj = FakeProjectService()

    # Input "1" → select proj2
    monkeypatch.setattr(builtins, "input", lambda _: "1")

    result = select_project(db, proj)
    assert result == "proj2"


def test_select_project_new_project(monkeypatch):
    db = FakeDB(projects=[
        {"name": "projA", "created_at": "T1"}
    ])
    proj = FakeProjectService()

    inputs = iter(["n", "NewProj"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    result = select_project(db, proj)
    assert result == "NewProj"
    assert "NewProj" in proj.created


def test_select_project_cancel(monkeypatch):
    db = FakeDB(projects=[])
    proj = FakeProjectService()

    monkeypatch.setattr(builtins, "input", lambda _: "x")
    res = select_project(db, proj)
    assert res is None


# -------------------------------------------------------------------
# TEST select_chat()
# -------------------------------------------------------------------
def test_select_chat_choose_existing(monkeypatch):
    db = FakeDB(
        projects=[{"name": "default", "created_at": "T"}],
        chats=[
            {"id": "c1", "title": "Chat1", "last_used": "T1", "project": "default"},
            {"id": "c2", "title": "Chat2", "last_used": "T2", "project": "default"},
        ],
    )
    chatsvc = FakeChatService()

    monkeypatch.setattr(builtins, "input", lambda _: "1")  # select c2
    res = select_chat(db, chatsvc, "default")

    assert res == "c2"


def test_select_chat_new_chat(monkeypatch):
    db = FakeDB(
        projects=[{"name": "default", "created_at": "T"}],
        chats=[],
    )
    chatsvc = FakeChatService()

    monkeypatch.setattr(builtins, "input", lambda _: "n")
    res = select_chat(db, chatsvc, "default")

    assert res == "chat-default-new"
    assert "default" in chatsvc.created


def test_select_chat_cancel(monkeypatch):
    db = FakeDB(
        projects=[{"name": "p", "created_at": "T"}],
        chats=[],
    )
    chatsvc = FakeChatService()

    monkeypatch.setattr(builtins, "input", lambda _: "x")
    res = select_chat(db, chatsvc, "p")
    assert res is None


# -------------------------------------------------------------------
# TEST chat history display
# -------------------------------------------------------------------
def test_show_chat_history(capsys):
    msgs = [
        {"role": "user", "content": "hello", "ts": "T1"},
        {"role": "assistant", "content": "hi", "ts": "T2"},
    ]
    svc = FakeMsgService(messages=msgs)

    show_chat_history(svc, "c1")

    out = capsys.readouterr().out
    assert "hello" in out
    assert "hi" in out
    assert "Chat History" in out


# -------------------------------------------------------------------
# TEST interactive_entry → returns dict for main.py
# -------------------------------------------------------------------
def test_interactive_entry_new_project_flow(monkeypatch):
    proj = FakeProjectService()
    chatsvc = FakeChatService()
    msgsvc = FakeMsgService()
    llm = object()
    settings = object()

    # Sequence:
    # choose "0" → new project
    # enter name
    # enter prompt
    inputs = iter(["0", "ProjX", "my first prompt"])

    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    resp = interactive_entry(
        db=FakeDB(), project_svc=proj,
        chat_svc=chatsvc, msg_svc=msgsvc,
        llm=llm, settings=settings
    )

    assert isinstance(resp, dict)
    assert resp["interactive_project"] == "ProjX"
    assert resp["interactive_chat"] == "chat-ProjX-new"
    assert resp["interactive_prompt"] == "my first prompt"
