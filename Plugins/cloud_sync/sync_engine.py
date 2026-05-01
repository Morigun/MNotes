from __future__ import annotations

import uuid
from datetime import datetime
from typing import Callable

from database.models import Note, Category, Tag
from database.repository import Repository


class SyncEngine:
    def __init__(self, repo: Repository, api_client):
        self._repo = repo
        self._api = api_client
        self._on_progress: Callable[[str], None] | None = None
        self._cancelled = False

    def set_progress_callback(self, cb: Callable[[str], None]):
        self._on_progress = cb

    def cancel(self):
        self._cancelled = True

    def _progress(self, msg: str):
        if self._on_progress:
            self._on_progress(msg)

    def sync(self, last_sync: str) -> dict:
        self._cancelled = False
        stats = {"pushed": 0, "pulled": 0, "conflicts": 0, "errors": []}

        self._progress("Миграция UUID...")
        self._migrate_uuids()

        self._progress("Авторизация...")
        self._api.authenticate()

        self._progress("Сбор локальных изменений...")
        push_data, push_files = self._collect_push_data(last_sync)

        self._progress("Отправка изменений...")
        if self._cancelled:
            return stats
        if push_data.get("notes") or push_data.get("categories") or push_data.get("tags") or push_data.get("note_tags") or push_data.get("deleted"):
            result = self._api.push_changes(push_data, push_files if push_files else None)
            stats["pushed"] = result.get("pushed", 0)
            stats["conflicts"] = len(result.get("conflicts", []))

        self._progress("Получение изменений...")
        if self._cancelled:
            return stats
        pull_data = self._api.pull_changes(last_sync)

        self._progress("Применение изменений...")
        if self._cancelled:
            return stats
        pulled = self._apply_pull_data(pull_data)
        stats["pulled"] = pulled

        self._progress("Загрузка файлов...")
        if self._cancelled:
            return stats
        self._download_files(pull_data.get("notes", []))

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self._progress(f"Синхронизация завершена: {now}")
        stats["last_sync"] = now
        return stats

    def _migrate_uuids(self):
        for note in self._repo.get_notes_without_uuid():
            self._repo.assign_sync_uuid("notes", note.id, str(uuid.uuid4()))
        for cat in self._repo.get_categories_without_uuid():
            self._repo.assign_sync_uuid("categories", cat.id, str(uuid.uuid4()))
        for tag in self._repo.get_tags_without_uuid():
            self._repo.assign_sync_uuid("tags", tag.id, str(uuid.uuid4()))

    def _collect_push_data(self, last_sync: str) -> tuple[dict, dict | None]:
        notes_data = []
        files = {}
        modified_notes = self._repo.get_notes_modified_since(last_sync) if last_sync else []
        all_notes = self._repo.get_notes(is_deleted=0, show_all_parents=True) + self._repo.get_notes(is_deleted=1, show_all_parents=True) if not last_sync else []
        notes_to_push = modified_notes if last_sync else all_notes

        cat_map = {c.id: c for c in self._repo.get_all_categories()}

        for note in notes_to_push:
            if not note.sync_uuid:
                continue
            entry = {
                "sync_uuid": note.sync_uuid,
                "title": note.title,
                "type": note.type,
                "is_pinned": note.is_pinned,
                "is_deleted": note.is_deleted,
                "is_encrypted": note.is_encrypted,
                "password_hash": note.password_hash,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
                "reminder_at": note.reminder_at,
                "reminder_repeat": note.reminder_repeat,
                "sort_order": note.sort_order,
                "deleted_parent_name": note.deleted_parent_name,
            }
            if note.category_id:
                c = cat_map.get(note.category_id)
                if c and c.sync_uuid:
                    entry["category_uuid"] = c.sync_uuid
            if note.parent_id:
                parent = self._repo.get_note(note.parent_id)
                if parent and parent.sync_uuid:
                    entry["parent_uuid"] = parent.sync_uuid
            if note.content is not None:
                files[f"file_{note.sync_uuid}"] = note.content
                entry["has_file"] = True
            notes_data.append(entry)

        categories_data = []
        if last_sync:
            modified_cats = self._repo.get_categories_modified_since(last_sync)
        else:
            modified_cats = self._repo.get_all_categories()
        for cat in modified_cats:
            if not cat.sync_uuid:
                continue
            categories_data.append({
                "sync_uuid": cat.sync_uuid,
                "name": cat.name,
                "color": cat.color,
                "updated_at": cat.updated_at or "",
            })

        tags_data = []
        if last_sync:
            modified_tags = self._repo.get_tags_modified_since(last_sync)
        else:
            modified_tags = self._repo.get_all_tags()
        for tag in modified_tags:
            if not tag.sync_uuid:
                continue
            tags_data.append({
                "sync_uuid": tag.sync_uuid,
                "name": tag.name,
                "updated_at": tag.updated_at or "",
            })

        note_uuids = [n["sync_uuid"] for n in notes_data]
        note_tags_data = self._repo.get_note_tags_by_sync_uuids(note_uuids)

        deleted_uuids = []
        if last_sync:
            deleted_notes = [n for n in notes_to_push if n.is_deleted]
            deleted_uuids = [n.sync_uuid for n in deleted_notes if n.sync_uuid]

        data = {
            "notes": notes_data,
            "categories": categories_data,
            "tags": tags_data,
            "note_tags": note_tags_data,
            "deleted": deleted_uuids,
        }
        return data, files if files else None

    def _apply_pull_data(self, pull_data: dict) -> int:
        count = 0
        for cat_data in pull_data.get("categories", []):
            if self._cancelled:
                break
            try:
                self._repo.upsert_category_by_sync_uuid(cat_data)
                count += 1
            except Exception:
                pass

        for tag_data in pull_data.get("tags", []):
            if self._cancelled:
                break
            try:
                self._repo.upsert_tag_by_sync_uuid(tag_data)
                count += 1
            except Exception:
                pass

        for note_data in pull_data.get("notes", []):
            if self._cancelled:
                break
            try:
                existing = self._repo.find_note_by_sync_uuid(note_data["sync_uuid"])
                if existing and existing.updated_at and note_data.get("updated_at"):
                    local_ts = existing.updated_at
                    remote_ts = note_data["updated_at"]
                    if local_ts >= remote_ts:
                        continue
                note_data.pop("has_file", None)
                self._repo.upsert_note_by_sync_uuid(note_data)
                count += 1
            except Exception:
                pass

        for nt in pull_data.get("note_tags", []):
            if self._cancelled:
                break
            try:
                note_uuid = nt.get("note_uuid")
                tag_uuid = nt.get("tag_uuid")
                if note_uuid and tag_uuid:
                    self._repo.set_note_tags_by_uuids(note_uuid, [tag_uuid])
            except Exception:
                pass

        for del_uuid in pull_data.get("deleted_ids", []):
            if self._cancelled:
                break
            try:
                existing = self._repo.find_note_by_sync_uuid(del_uuid)
                if existing and not existing.is_deleted:
                    self._repo.soft_delete_by_sync_uuid(del_uuid)
            except Exception:
                pass

        return count

    def _download_files(self, notes_data: list[dict]):
        for note_data in notes_data:
            if self._cancelled:
                break
            if not note_data.get("has_file"):
                continue
            sync_uuid = note_data.get("sync_uuid")
            if not sync_uuid:
                continue
            try:
                content = self._api.download_file(sync_uuid)
                existing = self._repo.find_note_by_sync_uuid(sync_uuid)
                if existing:
                    existing.content = content
                    self._repo.update_note(existing)
            except Exception:
                pass
