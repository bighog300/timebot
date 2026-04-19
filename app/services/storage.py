import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.config import settings


class StorageService:
    def __init__(self):
        self.upload_path = Path(settings.UPLOAD_PATH)
        self.processed_path = Path(settings.PROCESSED_PATH)
        self.text_path = self.processed_path / "text"
        self.thumbnail_path = self.processed_path / "thumbnails"
        self._ensure_directories()

    def _ensure_directories(self):
        for p in [self.upload_path, self.text_path, self.thumbnail_path]:
            p.mkdir(parents=True, exist_ok=True)

    def _dated_dir(self, base: Path) -> Path:
        dated = base / datetime.now().strftime("%Y/%m/%d")
        dated.mkdir(parents=True, exist_ok=True)
        return dated

    async def save_upload(self, file: UploadFile) -> tuple[Path, int]:
        content = await file.read()
        file_size = len(content)

        name_hash = hashlib.md5(
            f"{file.filename}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]
        stem = Path(file.filename).stem
        suffix = Path(file.filename).suffix
        safe_name = f"{stem}_{name_hash}{suffix}"

        dest = self._dated_dir(self.upload_path) / safe_name
        async with aiofiles.open(dest, "wb") as f:
            await f.write(content)

        return dest, file_size

    def save_text(self, document_id: str, text: str) -> Path:
        dest = self._dated_dir(self.text_path) / f"{document_id}.txt"
        dest.write_text(text, encoding="utf-8")
        return dest

    def save_thumbnail(self, document_id: str, image_data: bytes) -> Path:
        dest = self._dated_dir(self.thumbnail_path) / f"{document_id}.jpg"
        dest.write_bytes(image_data)
        return dest

    def get_mime_type(self, file_path: Path) -> str:
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or "application/octet-stream"

    def delete_file(self, file_path: str) -> bool:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            return True
        return False


storage = StorageService()
