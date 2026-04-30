from __future__ import annotations

import sys
from uuid import UUID

from app.config import settings
from app.db.base import SessionLocal
from app.models.document import Document
from app.services.document_processor import document_processor


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m app.scripts.process_document <document_id>")
        return 2

    try:
        document_id = UUID(sys.argv[1])
    except ValueError:
        print("Invalid document_id (must be UUID)")
        return 2

    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            print(f"Document not found: {document_id}")
            return 1

        print(f"document_id={document.id}")
        print(f"ai_configured={bool(settings.OPENAI_API_KEY)}")
        document_processor.process_document(db, document)
        db.refresh(document)
        print(f"processing_status={document.processing_status}")
        print(f"extracted_text_length={len(document.raw_text or '')}")
        print(f"summary_length={len(document.summary or '')}")
        print(f"processing_error={document.processing_error or ''}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
