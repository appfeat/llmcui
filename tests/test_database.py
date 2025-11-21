import os
import tempfile
from core.db.database import Database, init_db

def test_init_db_creates_file_and_tables():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")

        # DB should not exist initially
        assert not os.path.exists(db_path)

        # Initialize DB
        init_db(db_path)

        # DB file should now exist
        assert os.path.exists(db_path)

        # Check if tables exist
        db = Database(db_path)
        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}

        expected = {
            "projects",
            "chats",
            "messages",
            "distilled",
            "debug_log"
        }

        assert expected.issubset(tables)
        conn.close()
