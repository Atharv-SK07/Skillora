import sqlite3
from db import get_db


class TestDatabase:
    """Test database operations."""

    def test_get_db_returns_same_connection(self, app):
        """get_db returns the same connection within a request."""
        with app.app_context():
            db = get_db()
            assert db is get_db()  # Same object

    def test_init_db_command(self, runner):
        """init-db CLI command works."""
        result = runner.invoke(args=['init-db'])
        assert 'Initialized' in result.output or 'initialized' in result.output.lower()

    def test_users_table_exists(self, app):
        """Users table exists after init."""
        with app.app_context():
            db = get_db()
            result = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone()
            assert result is not None

    def test_career_selections_table_exists(self, app):
        """Career selections table exists after init."""
        with app.app_context():
            db = get_db()
            result = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='career_selections'").fetchone()
            assert result is not None

    def test_upgrade_schema_adds_missing_career_id(self, app, tmp_path):
        """upgrade_schema adds career_id column to legacy career_selections table and backfills."""
        from db import upgrade_schema
        # Create a fresh isolated sqlite connection simulating legacy Milestone 1 table
        legacy_db_path = str(tmp_path / "legacy.db")
        conn = sqlite3.connect(legacy_db_path)
        conn.row_factory = sqlite3.Row
        
        # Create legacy table without career_id
        conn.execute("""
            CREATE TABLE career_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                career_path TEXT NOT NULL,
                selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        # Create careers table
        conn.execute("""
            CREATE TABLE careers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL
            )
        """)
        conn.execute("INSERT INTO careers (code, title) VALUES ('frontend', 'Frontend Developer')")
        conn.execute("INSERT INTO career_selections (user_id, career_path, is_active) VALUES (1, 'Frontend Developer', 1)")
        conn.commit()

        # Check that career_id does not exist initially
        cols_before = [r['name'] for r in conn.execute("PRAGMA table_info(career_selections)").fetchall()]
        assert 'career_id' not in cols_before

        # Run upgrade_schema
        upgrade_schema(conn)

        # Check that career_id now exists and backfilled
        cols_after = [r['name'] for r in conn.execute("PRAGMA table_info(career_selections)").fetchall()]
        assert 'career_id' in cols_after

        row = conn.execute("SELECT cs.career_id, cs.career_path FROM career_selections cs WHERE id = 1").fetchone()
        assert row['career_id'] == 1

        # Running again is idempotent and does not raise
        upgrade_schema(conn)
        conn.close()

