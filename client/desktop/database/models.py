from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Category:
    id: Optional[int] = None
    name: str = ""
    color: str = "#ffffff"
    sync_uuid: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> Category:
        return cls(
            id=row["id"],
            name=row["name"],
            color=row["color"],
            sync_uuid=row["sync_uuid"] if "sync_uuid" in row.keys() else None,
            updated_at=row["updated_at"] if "updated_at" in row.keys() else None,
        )


@dataclass
class Tag:
    id: Optional[int] = None
    name: str = ""
    sync_uuid: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> Tag:
        return cls(
            id=row["id"],
            name=row["name"],
            sync_uuid=row["sync_uuid"] if "sync_uuid" in row.keys() else None,
            updated_at=row["updated_at"] if "updated_at" in row.keys() else None,
        )


@dataclass
class Note:
    id: Optional[int] = None
    title: str = ""
    type: str = "text"
    content: Optional[bytes] = None
    category_id: Optional[int] = None
    is_pinned: int = 0
    is_deleted: int = 0
    is_encrypted: int = 0
    password_hash: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    reminder_at: Optional[str] = None
    reminder_repeat: Optional[str] = None
    sort_order: int = 0
    parent_id: Optional[int] = None
    sync_uuid: Optional[str] = None
    deleted_parent_name: Optional[str] = None
    tags: list[Tag] = field(default_factory=list)

    @classmethod
    def from_row(cls, row) -> Note:
        return cls(
            id=row["id"],
            title=row["title"],
            type=row["type"],
            content=row["content"],
            category_id=row["category_id"],
            is_pinned=row["is_pinned"],
            is_deleted=row["is_deleted"],
            is_encrypted=row["is_encrypted"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            reminder_at=row["reminder_at"],
            reminder_repeat=row["reminder_repeat"],
            sort_order=row["sort_order"],
            parent_id=row["parent_id"] if "parent_id" in row.keys() else None,
            sync_uuid=row["sync_uuid"] if "sync_uuid" in row.keys() else None,
            deleted_parent_name=row["deleted_parent_name"] if "deleted_parent_name" in row.keys() else None,
        )
