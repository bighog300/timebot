from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

from app.db.base import SessionLocal
from app.models.document import Document
from app.models.intelligence import DocumentIntelligence


def _bool(v: bool) -> str:
    return "true" if v else "false"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m app.scripts.inspect_document <document_id>")
        return 2

    try:
        doc_id = UUID(sys.argv[1])
    except ValueError:
        print("Invalid document_id (must be UUID)")
        return 2

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            print(f"document_id={doc_id}")
            print("exists=false")
            return 1

        intelligence = db.query(DocumentIntelligence).filter(DocumentIntelligence.document_id == doc.id).first()
        original_exists = bool(doc.original_path and Path(doc.original_path).exists())

        extracted_path = None
        extracted_exists = False
        extracted_len = 0
        for candidate in Path("artifacts/extracted_text").rglob(f"{doc.id}.txt"):
            extracted_path = candidate
            extracted_exists = candidate.exists()
            if extracted_exists:
                extracted_len = len(candidate.read_text(encoding="utf-8"))
            break

        print(f"document_id={doc.id}")
        print(f"filename={doc.filename}")
        print(f"status={doc.processing_status}")
        print(f"processing_error={doc.processing_error or ''}")
        print(f"original_path_exists={_bool(original_exists)}")
        print(f"extracted_text_path_exists={_bool(extracted_exists)}")
        print(f"extracted_text_path={extracted_path or ''}")
        print(f"extracted_text_length={extracted_len}")
        print(f"document_summary_length={len(doc.summary or '')}")
        print(f"intelligence_exists={_bool(intelligence is not None)}")
        print(f"intelligence_summary_length={len((intelligence.summary if intelligence else '') or '')}")
        print(f"intelligence_entities_keys={sorted(list((intelligence.entities or {}).keys())) if intelligence else []}")
        print(f"document_upload_date={doc.upload_date}")
        print(f"document_processed_date={doc.processed_date}")
        print(f"intelligence_generated_at={intelligence.generated_at if intelligence else None}")
        print(f"intelligence_updated_at={intelligence.updated_at if intelligence else None}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
