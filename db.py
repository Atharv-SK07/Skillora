"""Database utilities for Skillora."""

import os
import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    """Get a database connection for the current request.

    Returns the same connection if called multiple times within a request.
    """
    if 'db' not in g:
        db_path = current_app.config['DATABASE']
        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        # Enable foreign key support
        g.db.execute('PRAGMA foreign_keys = ON')
    return g.db


def close_db(e=None):
    """Close the database connection at the end of a request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def upgrade_schema(db=None):
    """Safely apply incremental schema migrations to existing databases.

    Ensures that existing databases created in earlier milestones are migrated
    with missing columns and tables while strictly preserving existing data.
    """
    if db is None:
        db = get_db()

    # Check if career_selections table exists
    table_check = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='career_selections'"
    ).fetchone()
    if not table_check:
        return

    # 1. Ensure career_selections table has career_id column
    columns = [row['name'] for row in db.execute("PRAGMA table_info(career_selections)").fetchall()]
    if 'career_id' not in columns:
        db.execute("ALTER TABLE career_selections ADD COLUMN career_id INTEGER REFERENCES careers(id)")
        db.commit()

        # Backfill career_id from careers table where career_path matches
        careers_table = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='careers'"
        ).fetchone()
        if careers_table:
            db.execute("""
                UPDATE career_selections
                SET career_id = (
                    SELECT c.id FROM careers c
                    WHERE c.title = career_selections.career_path OR c.code = career_selections.career_path
                    LIMIT 1
                )
                WHERE career_id IS NULL
            """)
            db.commit()

    # 2. Ensure idx_career_selections_active index exists
    db.execute("CREATE INDEX IF NOT EXISTS idx_career_selections_active ON career_selections(user_id, is_active)")
    db.commit()

    # 3. Ensure Milestone 4 tables exist: roadmaps and roadmap_tasks
    db.execute("""
        CREATE TABLE IF NOT EXISTS roadmaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            career_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (career_id) REFERENCES careers (id) ON DELETE CASCADE
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS roadmap_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roadmap_id INTEGER NOT NULL,
            skill_id INTEGER,
            stage TEXT NOT NULL CHECK (stage IN ('learn', 'practice', 'build', 'review')),
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            estimated_duration TEXT NOT NULL,
            recommended_order INTEGER NOT NULL,
            resource_title TEXT,
            resource_url TEXT,
            reason TEXT,
            is_project INTEGER DEFAULT 0 CHECK (is_project IN (0, 1)),
            is_completed INTEGER DEFAULT 0 CHECK (is_completed IN (0, 1)),
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (roadmap_id) REFERENCES roadmaps (id) ON DELETE CASCADE,
            FOREIGN KEY (skill_id) REFERENCES skills (id) ON DELETE SET NULL
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_roadmaps_user_career ON roadmaps(user_id, career_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_roadmaps_user_active ON roadmaps(user_id, is_active)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_roadmap ON roadmap_tasks(roadmap_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_stage ON roadmap_tasks(roadmap_id, stage)")
    db.commit()



def init_db():
    """Initialize the database from schema.sql."""
    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r') as f:
        db.executescript(f.read())
    upgrade_schema(db)


def seed_db():
    """Seed the database with default careers and skills."""
    from seeds import seed_careers_and_skills
    seed_careers_and_skills(get_db())


@click.command('init-db')
@with_appcontext
def init_db_command():
    """CLI command: Initialize the database schema and seed data."""
    init_db()
    seed_db()
    click.echo('Initialized and seeded the Skillora database.')


@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """CLI command: Seed careers and skills without dropping database."""
    init_db()
    seed_db()
    click.echo('Seeded careers and skills successfully.')


def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command)

    # Ensure schema upgrades are safely applied to existing database files on startup
    with app.app_context():
        try:
            upgrade_schema()
        except sqlite3.OperationalError:
            pass

