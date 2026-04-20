# Phase 1 Sprint 2: Lifecycle Integrity

## Goal
Harden upload, processing, and deletion behavior.

## Scope
- Streaming uploads
- Processing status semantics
- Full deletion cleanup
- Service-level lifecycle tests

## Tasks
- Refactor storage write path to chunked streaming
- Enforce file size during streaming and remove partial files on failure
- Mark extraction failures as failed, not completed
- Remove original file, derived artifacts, and embeddings on delete
- Add tests:
  - `tests/services/test_storage.py`
  - `tests/services/test_document_processor.py`
  - `tests/api/test_documents_delete.py`
  - `tests/services/test_document_cleanup.py`

## Definition of done
- Oversized files are rejected safely
- Processing states are accurate
- Delete is idempotent and complete
