# Phase 3 Sprint 3: Gmail Ingestion & Incremental Sync

## Goal
Expand ingestion and make sync durable.

## Scope
- Gmail ingestion
- Incremental sync state
- Deduplication
- Retry/recovery behavior

## Tasks
- Ingest emails and attachments into document pipeline
- Track sync cursors / timestamps
- Add document deduplication rules across sources
- Add sync retry paths and observability

## Definition of done
- Background sync updates the corpus without manual upload
