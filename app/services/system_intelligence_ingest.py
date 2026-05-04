import hashlib
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.system_intelligence import SystemIntelligenceChunk, SystemIntelligenceDocument
from app.services.text_extractor import text_extractor

CHUNK_SIZE = 1200
OVERLAP = 150


def _normalize_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.replace("\r\n", "\n").split("\n") if line.strip())


def _chunk_text(text: str) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + CHUNK_SIZE)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(start + 1, end - OVERLAP)
    return chunks


def ingest_document(db: Session, doc: SystemIntelligenceDocument) -> None:
    doc.extraction_status = "pending"
    doc.index_status = "pending"
    doc.extraction_error = None
    doc.index_error = None
    db.query(SystemIntelligenceChunk).filter(SystemIntelligenceChunk.system_document_id == doc.id).delete()
    db.flush()

    try:
        file_path = Path(doc.storage_uri or "")
        ext = file_path.suffix.lstrip(".").lower()
        text, _, _ = text_extractor.extract(file_path, ext)
        if not text:
            doc.extraction_status = "failed"
            doc.extraction_error = "No extractable text found"
            doc.index_status = "failed"
            doc.index_error = "Indexing skipped because extraction failed"
            return
        normalized = _normalize_text(text)
        doc.extraction_status = "extracted"
        chunks = _chunk_text(normalized)
        for idx, content in enumerate(chunks):
            db.add(SystemIntelligenceChunk(system_document_id=doc.id, chunk_index=idx, content=content, metadata_json={"length": len(content)}))
        doc.index_status = "indexed"
        doc.indexed_at = datetime.now(timezone.utc)
    except Exception as exc:
        doc.extraction_status = "failed"
        doc.index_status = "failed"
        doc.extraction_error = str(exc)
        doc.index_error = str(exc)


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
