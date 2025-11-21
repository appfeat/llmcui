import pytest
import sqlite3
import os

from core.db.database import init_db, Database

@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """Creates a temporary SQLite database for each test."""
    db_path = tmp_path / "test.db"

    # mock LLMCUI_ROOT so init_db writes nothing outside tmpdir
    monkeypatch.setenv("LLMCUI_ROOT", str(tmp_path))

    # initialize DB
    init_db(str(db_path))

    # return Database instance
    return Database(str(db_path))
