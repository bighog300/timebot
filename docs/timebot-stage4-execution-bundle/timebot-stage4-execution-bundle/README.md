# Timebot Stage 4 Execution Bundle

This bundle is a repo-specific execution package for completing **Stage 4 / Phase 4** of the Timebot Document Intelligence Platform.

## What this bundle is for

Stage 4 is the **frontend and productization phase**. Your repo already has:
- a working FastAPI backend
- document upload and processing
- categories, analysis, queue, search, semantic search, and websocket endpoints
- Stage 4 docs and UI specifications

What it does **not** yet have is the actual frontend application and several backend contracts the UI spec depends on.

This bundle is designed for **Codex** and assumes that:
1. Phase 3 updates are being implemented now.
2. Codex should build the Stage 4 app in a way that matches the current backend rather than blindly following the older docs.

## Files

- `CODEX_EXECUTION_PROMPT.md` — the primary prompt to hand to Codex
- `AGENTS.md` — repo-local instructions for Codex
- `STAGE4_GAP_REPORT.md` — what is missing today
- `STAGE4_WORKPLAN.md` — delivery order and milestones
- `BACKEND_CONTRACT_GAPS.md` — backend endpoints/UI contract issues that must be closed in Stage 4
- `VALIDATION_CHECKLIST.md` — acceptance criteria and test checklist

## Recommended use

1. Put `AGENTS.md` in the repo root.
2. Give Codex the contents of `CODEX_EXECUTION_PROMPT.md`.
3. Let Codex implement in milestones, committing after each green checkpoint.
4. Use `VALIDATION_CHECKLIST.md` to verify completion.

## Stage 4 completion definition

Stage 4 is complete when a user can:
- open the web app
- upload and browse documents
- watch processing progress live
- search by keyword and semantic mode
- view timeline/grid/list presentations
- inspect document details and related documents
- manage categories, insights, and connections
- use the app on desktop and mobile
- run the frontend test suite and production build successfully
