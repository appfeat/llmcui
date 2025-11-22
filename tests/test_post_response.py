import os
import tempfile
import pytest

from cli.interactive.post_response import post_response_menu


# --- Fake Services --------------------------------------------------

class FakeProjectService:
    pass


class FakeChatService:
    pass


class FakeMsgService:
    pass


class FakeLLM:
    pass


class FakeSettings:
    pass


# --- Helpers --------------------------------------------------------

def run_menu(monkeypatch, inputs, db="DB", proj="projA", chat="chat1"):
    """
    Simulates multiple sequential user inputs.
    Each call to ask() returns the next item from inputs.
    """
    input_iter = iter(inputs)
    monkeypatch.setattr(
        "cli.interactive.menu.ask",
        lambda prompt: next(input_iter)
    )

    # Mock project/chat selection calls
    monkeypatch.setattr(
        "cli.interactive.menu.select_project",
        lambda db, project_svc: "projB"
    )
    monkeypatch.setattr(
        "cli.interactive.menu.select_chat",
        lambda db, chat_svc, proj: "chatB"
    )
    monkeypatch.setattr(
        "cli.interactive.menu.show_chat_history",
        lambda msg_svc, chat: None
    )

    return post_response_menu(
        db,
        FakeProjectService(),
        FakeChatService(),
        FakeMsgService(),
        FakeLLM(),
        FakeSettings(),
        current_project=proj,
        current_chat=chat,
    )


# --- Tests ----------------------------------------------------------

def test_post_response_exit(monkeypatch):
    result = run_menu(monkeypatch, ["x"])
    assert result == 0


def test_post_response_ask_another(monkeypatch):
    result = run_menu(monkeypatch, ["a", "hello again"])
    assert result["interactive_project"] == "projA"
    assert result["interactive_chat"] == "chat1"
    assert result["interactive_prompt"] == "hello again"


def test_post_response_pipe_file(monkeypatch, tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("content123")

    result = run_menu(monkeypatch, ["f", str(f), "explain"])
    assert result["interactive_project"] == "projA"
    assert result["interactive_chat"] == "chat1"
    assert "content123" in result["interactive_prompt"]
    assert "explain" in result["interactive_prompt"]


def test_post_response_switch_chat(monkeypatch):
    result = run_menu(monkeypatch, ["c", "new question"])
    assert result["interactive_project"] == "projA"
    assert result["interactive_chat"] == "chatB"
    assert result["interactive_prompt"] == "new question"


def test_post_response_switch_project(monkeypatch):
    result = run_menu(monkeypatch, ["p", "new prompt"])
    assert result["interactive_project"] == "projB"
    assert result["interactive_chat"] == "chatB"
    assert result["interactive_prompt"] == "new prompt"
