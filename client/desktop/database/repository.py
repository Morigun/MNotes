from __future__ import annotations

import uuid
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
        if not note.sync_uuid:
            note.sync_uuid = str(uuid.uuid4())
        pid = note.parent_id if note.parent_id else None
        cur = self._conn.execute(
            """INSERT INTO notes (title, type, content, category_id, is_pinned,
               is_deleted, is_encrypted, password_hash, reminder_at, reminder_repeat,
               sort_order, parent_id, sync_uuid)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                note.title, note.type, note.content, note.category_id,
                note.is_pinned, note.is_deleted, note.is_encrypted,
                note.password_hash, note.reminder_at, note.reminder_repeat,
                note.sort_order, pid, note.sync_uuid,
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
        pid = note.parent_id if note.parent_id else None
        self._conn.execute(
            """UPDATE notes SET title=?, type=?, content=?, category_id=?,
               is_pinned=?, is_deleted=?, is_encrypted=?, password_hash=?,
               reminder_at=?, reminder_repeat=?, sort_order=?, parent_id=?,
               sync_uuid=?, deleted_parent_name=?,
               updated_at=datetime('now')
               WHERE id=?""",
            (
                note.title, note.type, note.content, note.category_id,
                note.is_pinned, note.is_deleted, note.is_encrypted,
                note.password_hash, note.reminder_at, note.reminder_repeat,
                note.sort_order, pid, note.sync_uuid,
                note.deleted_parent_name, note.id,
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
        sync_uuid = str(uuid.uuid4())
        cur = self._conn.execute(
            "INSERT INTO categories (name, color, sync_uuid) VALUES (?, ?, ?)",
            (name, color, sync_uuid),
        )
        self._conn.commit()
        return cur.lastrowid

    def update_category(self, category: Category) -> None:
        self._conn.execute(
            "UPDATE categories SET name=?, color=?, updated_at=datetime('now') WHERE id=?",
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
        sync_uuid = str(uuid.uuid4())
        cur = self._conn.execute(
            "INSERT INTO tags (name, sync_uuid) VALUES (?, ?)",
            (name, sync_uuid),
        )
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

    def get_all_folders(self) -> list[Note]:
        rows = self._conn.execute(
            "SELECT * FROM notes WHERE type='folder' AND is_deleted=0 ORDER BY title"
        ).fetchall()
        return [Note.from_row(r) for r in rows]

    def duplicate_note(self, note_id: int) -> int | None:
        row = self._conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
        if row is None:
            return None
        pid = row["parent_id"] if row["parent_id"] else None
        cur = self._conn.execute(
            """INSERT INTO notes (title, type, content, category_id, is_pinned,
               is_deleted, is_encrypted, password_hash, reminder_at, reminder_repeat,
               sort_order, parent_id, sync_uuid)
               VALUES (?, ?, ?, ?, 0, 0, 0, NULL, NULL, NULL, 0, ?, ?)""",
            (row["title"] + " (копия)", row["type"], row["content"],
             row["category_id"], pid, str(uuid.uuid4())),
        )
        self._conn.commit()
        return cur.lastrowid

    def get_notes_modified_since(self, since: str) -> list[Note]:
        rows = self._conn.execute(
            "SELECT * FROM notes WHERE updated_at > ? AND sync_uuid IS NOT NULL",
            (since,),
        ).fetchall()
        notes = [Note.from_row(r) for r in rows]
        for n in notes:
            n.tags = self._get_tags_for_note(n.id)
        return notes

    def get_categories_modified_since(self, since: str) -> list[Category]:
        rows = self._conn.execute(
            "SELECT * FROM categories WHERE updated_at > ? AND sync_uuid IS NOT NULL",
            (since,),
        ).fetchall()
        return [Category.from_row(r) for r in rows]

    def get_tags_modified_since(self, since: str) -> list[Tag]:
        rows = self._conn.execute(
            "SELECT * FROM tags WHERE updated_at > ? AND sync_uuid IS NOT NULL",
            (since,),
        ).fetchall()
        return [Tag.from_row(r) for r in rows]

    def get_note_tags_by_sync_uuids(self, note_uuids: list[str]) -> list[dict]:
        if not note_uuids:
            return []
        placeholders = ",".join("?" * len(note_uuids))
        rows = self._conn.execute(
            f"""SELECT n.sync_uuid AS note_uuid, t.sync_uuid AS tag_uuid
                FROM note_tags nt
                JOIN notes n ON n.id = nt.note_id
                JOIN tags t ON t.id = nt.tag_id
                WHERE n.sync_uuid IN ({placeholders})""",
            note_uuids,
        ).fetchall()
        return [{"note_uuid": r["note_uuid"], "tag_uuid": r["tag_uuid"]} for r in rows]

    def find_note_by_sync_uuid(self, sync_uuid: str) -> Optional[Note]:
        row = self._conn.execute(
            "SELECT * FROM notes WHERE sync_uuid = ?", (sync_uuid,)
        ).fetchone()
        if row is None:
            return None
        note = Note.from_row(row)
        note.tags = self._get_tags_for_note(note.id)
        return note

    def find_category_by_sync_uuid(self, sync_uuid: str) -> Optional[Category]:
        row = self._conn.execute(
            "SELECT * FROM categories WHERE sync_uuid = ?", (sync_uuid,)
        ).fetchone()
        return Category.from_row(row) if row else None

    def find_tag_by_sync_uuid(self, sync_uuid: str) -> Optional[Tag]:
        row = self._conn.execute(
            "SELECT * FROM tags WHERE sync_uuid = ?", (sync_uuid,)
        ).fetchone()
        return Tag.from_row(row) if row else None

    def find_category_by_name(self, name: str) -> Optional[Category]:
        row = self._conn.execute(
            "SELECT * FROM categories WHERE name = ?", (name,)
        ).fetchone()
        return Category.from_row(row) if row else None

    def find_tag_by_name(self, name: str) -> Optional[Tag]:
        row = self._conn.execute(
            "SELECT * FROM tags WHERE name = ?", (name,)
        ).fetchone()
        return Tag.from_row(row) if row else None

    def upsert_note_by_sync_uuid(self, data: dict) -> int:
        existing = self._conn.execute(
            "SELECT id FROM notes WHERE sync_uuid = ?", (data["sync_uuid"],)
        ).fetchone()
        if existing:
            self._conn.execute(
                """UPDATE notes SET title=?, type=?, content=?, is_pinned=?,
                   is_deleted=?, is_encrypted=?, password_hash=?,
                   reminder_at=?, reminder_repeat=?, sort_order=?,
                   deleted_parent_name=?, updated_at=?
                   WHERE sync_uuid=?""",
                (
                    data.get("title", ""),
                    data.get("type", "text"),
                    data.get("content"),
                    data.get("is_pinned", 0),
                    data.get("is_deleted", 0),
                    data.get("is_encrypted", 0),
                    data.get("password_hash"),
                    data.get("reminder_at"),
                    data.get("reminder_repeat"),
                    data.get("sort_order", 0),
                    data.get("deleted_parent_name"),
                    data.get("updated_at"),
                    data["sync_uuid"],
                ),
            )
            self._conn.commit()
            return existing["id"]
        parent_id = None
        if data.get("parent_uuid"):
            parent = self.find_note_by_sync_uuid(data["parent_uuid"])
            if parent:
                parent_id = parent.id
        category_id = None
        if data.get("category_uuid"):
            cat = self.find_category_by_sync_uuid(data["category_uuid"])
            if cat:
                category_id = cat.id
        cur = self._conn.execute(
            """INSERT INTO notes (title, type, content, category_id, is_pinned,
               is_deleted, is_encrypted, password_hash, created_at, updated_at,
               reminder_at, reminder_repeat, sort_order, parent_id, sync_uuid,
               deleted_parent_name)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data.get("title", ""),
                data.get("type", "text"),
                data.get("content"),
                category_id,
                data.get("is_pinned", 0),
                data.get("is_deleted", 0),
                data.get("is_encrypted", 0),
                data.get("password_hash"),
                data.get("created_at"),
                data.get("updated_at"),
                data.get("reminder_at"),
                data.get("reminder_repeat"),
                data.get("sort_order", 0),
                parent_id,
                data["sync_uuid"],
                data.get("deleted_parent_name"),
            ),
        )
        self._conn.commit()
        return cur.lastrowid

    def upsert_category_by_sync_uuid(self, data: dict) -> int:
        existing = self._conn.execute(
            "SELECT id FROM categories WHERE sync_uuid = ?", (data["sync_uuid"],)
        ).fetchone()
        if existing:
            self._conn.execute(
                "UPDATE categories SET name=?, color=?, updated_at=? WHERE sync_uuid=?",
                (data.get("name", ""), data.get("color", "#ffffff"),
                 data.get("updated_at"), data["sync_uuid"]),
            )
            self._conn.commit()
            return existing["id"]
        cur = self._conn.execute(
            "INSERT INTO categories (name, color, sync_uuid) VALUES (?, ?, ?)",
            (data.get("name", ""), data.get("color", "#ffffff"), data["sync_uuid"]),
        )
        self._conn.commit()
        return cur.lastrowid

    def upsert_tag_by_sync_uuid(self, data: dict) -> int:
        existing = self._conn.execute(
            "SELECT id FROM tags WHERE sync_uuid = ?", (data["sync_uuid"],)
        ).fetchone()
        if existing:
            self._conn.execute(
                "UPDATE tags SET name=?, updated_at=? WHERE sync_uuid=?",
                (data.get("name", ""), data.get("updated_at"), data["sync_uuid"]),
            )
            self._conn.commit()
            return existing["id"]
        cur = self._conn.execute(
            "INSERT INTO tags (name, sync_uuid) VALUES (?, ?)",
            (data.get("name", ""), data["sync_uuid"]),
        )
        self._conn.commit()
        return cur.lastrowid

    def set_note_tags_by_uuids(self, note_sync_uuid: str, tag_sync_uuids: list[str]):
        note = self.find_note_by_sync_uuid(note_sync_uuid)
        if not note:
            return
        tag_ids = []
        for tu in tag_sync_uuids:
            t = self.find_tag_by_sync_uuid(tu)
            if t:
                tag_ids.append(t.id)
        self.set_note_tags(note.id, tag_ids)

    def get_notes_without_uuid(self) -> list[Note]:
        rows = self._conn.execute(
            "SELECT * FROM notes WHERE sync_uuid IS NULL"
        ).fetchall()
        return [Note.from_row(r) for r in rows]

    def get_categories_without_uuid(self) -> list[Category]:
        rows = self._conn.execute(
            "SELECT * FROM categories WHERE sync_uuid IS NULL"
        ).fetchall()
        return [Category.from_row(r) for r in rows]

    def get_tags_without_uuid(self) -> list[Tag]:
        rows = self._conn.execute(
            "SELECT * FROM tags WHERE sync_uuid IS NULL"
        ).fetchall()
        return [Tag.from_row(r) for r in rows]

    def assign_sync_uuid(self, table: str, row_id: int, sync_uuid: str):
        self._conn.execute(
            f"UPDATE {table} SET sync_uuid = ? WHERE id = ?",
            (sync_uuid, row_id),
        )
        self._conn.commit()

    def soft_delete_by_sync_uuid(self, sync_uuid: str):
        self._conn.execute(
            "UPDATE notes SET is_deleted=1, updated_at=datetime('now') WHERE sync_uuid=?",
            (sync_uuid,),
        )
        self._conn.commit()
