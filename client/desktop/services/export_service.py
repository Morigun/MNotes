from __future__ import annotations

import json
import zipfile
import io
from pathlib import Path
from typing import Optional

from database.models import Note
from database.repository import Repository


class ExportService:
    def __init__(self, repo: Repository):
        self._repo = repo

    def export_note(self, note: Note, path: str) -> None:
        p = Path(path)
        if note.type == "text":
            p = p.with_suffix(".txt")
            p.write_bytes(note.content or b"")
        elif note.type == "markdown":
            p = p.with_suffix(".md")
            p.write_bytes(note.content or b"")
        elif note.type == "richtext":
            p = p.with_suffix(".html")
            p.write_bytes(note.content or b"")
        elif note.type == "list":
            p = p.with_suffix(".txt")
            items = json.loads((note.content or b"[]").decode("utf-8", errors="replace"))
            lines = [f"[{'x' if it.get('checked') else ' '}] {it.get('text', '')}" for it in items]
            p.write_text("\n".join(lines), encoding="utf-8")
        elif note.type == "audio":
            p = p.with_suffix(".wav")
            p.write_bytes(note.content or b"")
        elif note.type == "image":
            if note.content and note.content[:4] == b"\x89PNG":
                p = p.with_suffix(".png")
            else:
                p = p.with_suffix(".jpg")
            p.write_bytes(note.content or b"")
        elif note.type == "table":
            p = p.with_suffix(".csv")
            import json
            payload = json.loads((note.content or b'{"headers":[],"rows":[]}').decode("utf-8", errors="replace"))
            headers = payload.get("headers", [])
            rows = payload.get("rows", [])
            import csv, io
            buf = io.StringIO()
            writer = csv.writer(buf, lineterminator="\n")
            writer.writerow(headers)
            writer.writerows(rows)
            p.write_text(buf.getvalue(), encoding="utf-8")

    def export_all(self, zip_path: str) -> None:
        notes = self._repo.get_notes()
        index = []
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for note in notes:
                ext = {"text": ".txt", "markdown": ".md", "richtext": ".html",
                       "list": ".txt", "audio": ".wav", "image": ".png",
                       "table": ".csv"}.get(note.type, ".bin")
                filename = f"notes/{note.id}_{note.title or 'untitled'}{ext}"
                if note.content:
                    zf.writestr(filename, note.content)
                entry = {
                    "id": note.id, "title": note.title, "type": note.type,
                    "filename": filename if note.content else None,
                    "is_pinned": note.is_pinned, "created_at": note.created_at,
                }
                index.append(entry)
            zf.writestr("index.json", json.dumps(index, ensure_ascii=False, indent=2))

    def import_from_zip(self, zip_path: str) -> int:
        count = 0
        with zipfile.ZipFile(zip_path, "r") as zf:
            if "index.json" not in zf.namelist():
                return 0
            index = json.loads(zf.read("index.json"))
            for entry in index:
                content = b""
                if entry.get("filename"):
                    content = zf.read(entry["filename"])
                note = Note(
                    title=entry.get("title", ""),
                    type=entry.get("type", "text"),
                    content=content,
                    is_pinned=entry.get("is_pinned", 0),
                )
                self._repo.create_note(note)
                count += 1
        return count
