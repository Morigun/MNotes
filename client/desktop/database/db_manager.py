import sqlite3
import sys
from pathlib import Path


def _db_path() -> Path:
    if getattr(sys, 'frozen', False):
        app_data = Path.home() / "AppData" / "Local" / "MNotes"
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data / "mnotes.db"
    return Path(__file__).resolve().parent.parent / "mnotes.db"


DB_PATH = _db_path()

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    color       TEXT DEFAULT '#ffffff'
);

CREATE TABLE IF NOT EXISTS tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS notes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL DEFAULT '',
    type            TEXT NOT NULL,
    content         BLOB,
    category_id     INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    is_pinned       INTEGER DEFAULT 0,
    is_deleted      INTEGER DEFAULT 0,
    is_encrypted    INTEGER DEFAULT 0,
    password_hash   TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now')),
    reminder_at     TEXT,
    reminder_repeat TEXT,
    sort_order      INTEGER DEFAULT 0,
    parent_id       INTEGER REFERENCES notes(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS note_tags (
    note_id INTEGER REFERENCES notes(id) ON DELETE CASCADE,
    tag_id  INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (note_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_notes_type ON notes(type);
CREATE INDEX IF NOT EXISTS idx_notes_deleted ON notes(is_deleted);
CREATE INDEX IF NOT EXISTS idx_notes_reminder ON notes(reminder_at);
CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category_id);
CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at);
"""


class DatabaseManager:
    _instance = None

    def __new__(cls, db_path=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connection = None
            cls._instance._db_path = Path(db_path) if db_path else DB_PATH
        return cls._instance

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys=ON")
            self._create_tables()
        return self._connection

    def _create_tables(self):
        self._connection.executescript(SCHEMA)
        self._migrate()

    def _migrate(self):
        cols = [r[1] for r in self._connection.execute("PRAGMA table_info(notes)").fetchall()]
        if "parent_id" not in cols:
            self._connection.execute(
                "ALTER TABLE notes ADD COLUMN parent_id INTEGER REFERENCES notes(id) ON DELETE SET NULL"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_notes_parent ON notes(parent_id)"
            )
        if "deleted_parent_name" not in cols:
            self._connection.execute(
                "ALTER TABLE notes ADD COLUMN deleted_parent_name TEXT"
            )
        if "sync_uuid" not in cols:
            self._connection.execute(
                "ALTER TABLE notes ADD COLUMN sync_uuid CHAR(36)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_notes_sync_uuid ON notes(sync_uuid)"
            )

        cat_cols = [r[1] for r in self._connection.execute("PRAGMA table_info(categories)").fetchall()]
        if "sync_uuid" not in cat_cols:
            self._connection.execute(
                "ALTER TABLE categories ADD COLUMN sync_uuid CHAR(36)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_categories_sync_uuid ON categories(sync_uuid)"
            )

        tag_cols = [r[1] for r in self._connection.execute("PRAGMA table_info(tags)").fetchall()]
        if "sync_uuid" not in tag_cols:
            self._connection.execute(
                "ALTER TABLE tags ADD COLUMN sync_uuid CHAR(36)"
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_tags_sync_uuid ON tags(sync_uuid)"
            )
        if "updated_at" not in tag_cols:
            self._connection.execute(
                "ALTER TABLE tags ADD COLUMN updated_at TEXT"
            )
            self._connection.execute(
                "UPDATE tags SET updated_at = datetime('now') WHERE updated_at IS NULL"
            )

        if "updated_at" not in cat_cols:
            self._connection.execute(
                "ALTER TABLE categories ADD COLUMN updated_at TEXT"
            )
            self._connection.execute(
                "UPDATE categories SET updated_at = datetime('now') WHERE updated_at IS NULL"
            )

        self._connection.commit()

    def init_db(self):
        _ = self.connection

    def close(self):
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    @classmethod
    def reset(cls):
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None
