"""Generate embeddings for existing processed documents."""

from app.db.base import SessionLocal
from app.models.document import Document
from app.workers.tasks import embed_document_task


def generate_all_embeddings():
    db = SessionLocal()
    try:
        documents = db.query(Document).filter(Document.processing_status == "completed").all()
        for document in documents:
            embed_document_task.delay(str(document.id))
            print(f"Queued embedding for {document.filename}")
        print(f"Queued {len(documents)} documents for embedding")
    finally:
        db.close()


if __name__ == "__main__":
    generate_all_embeddings()
