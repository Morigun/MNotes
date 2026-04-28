from __future__ import annotations

from typing import Optional

from database.db_manager import DatabaseManager
from database.models import Category, Note, Tag


class Repository:
    def __init__(self, db: DatabaseManager | None = None):
        self._db = db or DatabaseManager()

    @property
    def _conn(self):
        return self._db.connection

    def create_note(self, note: Note) -> int:
        cur = self._conn.execute(
            """INSERT INTO notes (title, type, content, category_id, is_pinned,
               is_deleted, is_encrypted, password_hash, reminder_at, reminder_repeat,
               sort_order, parent_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                note.title, note.type, note.content, note.category_id,
                note.is_pinned, note.is_deleted, note.is_encrypted,
                note.password_hash, note.reminder_at, note.reminder_repeat,
                note.sort_order, note.parent_id,
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_note(self, note_id: int) -> Optional[Note]:
        row = self._conn.execute(
            "SELECT * FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        if row is None:
            return None
        note = Note.from_row(row)
        note.tags = self._get_tags_for_note(note_id)
        return note

    def get_notes(
        self,
        *,
        is_deleted: int = 0,
        note_type: Optional[str] = None,
        category_id: Optional[int] = None,
        tag_id: Optional[int] = None,
        search: Optional[str] = None,
        date: Optional[str] = None,
        parent_id: Optional[int | None] = 0,
        show_all_parents: bool = False,
    ) -> list[Note]:
        query = "SELECT * FROM notes WHERE is_deleted = ?"
        params: list = [is_deleted]

        if not show_all_parents:
            if parent_id == 0:
                query += " AND parent_id IS NULL"
            elif parent_id is not None:
                query += " AND parent_id = ?"
                params.append(parent_id)

        if note_type is not None:
            query += " AND type = ?"
            params.append(note_type)

        if category_id is not None:
            query += " AND category_id = ?"
            params.append(category_id)

        if tag_id is not None:
            query += (
                " AND id IN (SELECT note_id FROM note_tags WHERE tag_id = ?)"
            )
            params.append(tag_id)

        if search:
            query += " AND (title LIKE ? OR CAST(content AS TEXT) LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        if date:
            query += " AND (DATE(created_at) = ? OR DATE(REPLACE(reminder_at, 'T', ' ')) = ?)"
            params.extend([date, date])

        query += " ORDER BY is_pinned DESC, updated_at DESC"

        rows = self._conn.execute(query, params).fetchall()
        notes = [Note.from_row(r) for r in rows]
        for n in notes:
            n.tags = self._get_tags_for_note(n.id)
        return notes

    def update_note(self, note: Note) -> None:
        self._conn.execute(
            """UPDATE notes SET title=?, type=?, content=?, category_id=?,
               is_pinned=?, is_deleted=?, is_encrypted=?, password_hash=?,
               reminder_at=?, reminder_repeat=?, sort_order=?, parent_id=?,
               updated_at=datetime('now')
               WHERE id=?""",
            (
                note.title, note.type, note.content, note.category_id,
                note.is_pinned, note.is_deleted, note.is_encrypted,
                note.password_hash, note.reminder_at, note.reminder_repeat,
                note.sort_order, note.parent_id, note.id,
            ),
        )
        self._conn.commit()

    def soft_delete_note(self, note_id: int) -> None:
        self._conn.execute(
            "UPDATE notes SET is_deleted=1, updated_at=datetime('now') WHERE id=?",
            (note_id,),
        )
        self._conn.commit()

    def restore_note(self, note_id: int) -> None:
        self._conn.execute(
            "UPDATE notes SET is_deleted=0, updated_at=datetime('now') WHERE id=?",
            (note_id,),
        )
        self._conn.commit()

    def delete_note_permanent(self, note_id: int) -> None:
        self._conn.execute("DELETE FROM note_tags WHERE note_id=?", (note_id,))
        self._conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
        self._conn.commit()

    def delete_all_trashed(self) -> None:
        self._conn.execute(
            "DELETE FROM note_tags WHERE note_id IN "
            "(SELECT id FROM notes WHERE is_deleted=1)"
        )
        self._conn.execute("DELETE FROM notes WHERE is_deleted=1")
        self._conn.commit()

    def set_note_tags(self, note_id: int, tag_ids: list[int]) -> None:
        self._conn.execute(
            "DELETE FROM note_tags WHERE note_id=?", (note_id,)
        )
        for tid in tag_ids:
            self._conn.execute(
                "INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)",
                (note_id, tid),
            )
        self._conn.commit()

    def _get_tags_for_note(self, note_id: int) -> list[Tag]:
        rows = self._conn.execute(
            """SELECT t.* FROM tags t
               JOIN note_tags nt ON t.id = nt.tag_id
               WHERE nt.note_id = ?""",
            (note_id,),
        ).fetchall()
        return [Tag.from_row(r) for r in rows]

    def move_note_to_folder(self, note_id: int, folder_id: int) -> None:
        self._conn.execute(
            "UPDATE notes SET parent_id=?, updated_at=datetime('now') WHERE id=?",
            (folder_id, note_id),
        )
        self._conn.commit()

    def remove_note_from_folder(self, note_id: int) -> None:
        self._conn.execute(
            "UPDATE notes SET parent_id=NULL, updated_at=datetime('now') WHERE id=?",
            (note_id,),
        )
        self._conn.commit()

    def get_folder_child_count(self, folder_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM notes WHERE parent_id=? AND is_deleted=0",
            (folder_id,),
        ).fetchone()
        return row["cnt"] if row else 0

    def get_all_categories(self) -> list[Category]:
        rows = self._conn.execute(
            "SELECT * FROM categories ORDER BY name"
        ).fetchall()
        return [Category.from_row(r) for r in rows]

    def create_category(self, name: str, color: str = "#ffffff") -> int:
        cur = self._conn.execute(
            "INSERT INTO categories (name, color) VALUES (?, ?)",
            (name, color),
        )
        self._conn.commit()
        return cur.lastrowid

    def update_category(self, category: Category) -> None:
        self._conn.execute(
            "UPDATE categories SET name=?, color=? WHERE id=?",
            (category.name, category.color, category.id),
        )
        self._conn.commit()

    def delete_category(self, category_id: int) -> None:
        self._conn.execute("DELETE FROM categories WHERE id=?", (category_id,))
        self._conn.commit()

    def get_all_tags(self) -> list[Tag]:
        rows = self._conn.execute("SELECT * FROM tags ORDER BY name").fetchall()
        return [Tag.from_row(r) for r in rows]

    def create_tag(self, name: str) -> int:
        cur = self._conn.execute("INSERT INTO tags (name) VALUES (?)", (name,))
        self._conn.commit()
        return cur.lastrowid

    def delete_tag(self, tag_id: int) -> None:
        self._conn.execute("DELETE FROM note_tags WHERE tag_id=?", (tag_id,))
        self._conn.execute("DELETE FROM tags WHERE id=?", (tag_id,))
        self._conn.commit()

    def get_tag_note_counts(self) -> dict[int, int]:
        rows = self._conn.execute(
            """SELECT tag_id, COUNT(*) as cnt FROM note_tags
               GROUP BY tag_id"""
        ).fetchall()
        return {r["tag_id"]: r["cnt"] for r in rows}

    def get_dates_with_notes(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT DATE(created_at) as d FROM notes WHERE is_deleted=0"
        ).fetchall()
        return [r["d"] for r in rows if r["d"]]

    def get_dates_with_reminders(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT DATE(reminder_at) as d FROM notes WHERE reminder_at IS NOT NULL AND is_deleted=0"
        ).fetchall()
        return [r["d"] for r in rows if r["d"]]

    def get_pending_reminders(self) -> list[Note]:
        rows = self._conn.execute(
            """SELECT * FROM notes
               WHERE reminder_at IS NOT NULL
               AND REPLACE(reminder_at, 'T', ' ') <= datetime('now', 'localtime')
               AND is_deleted = 0
               ORDER BY reminder_at"""
        ).fetchall()
        return [Note.from_row(r) for r in rows]
