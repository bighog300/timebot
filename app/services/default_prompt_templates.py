from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DefaultPromptTemplate:
    type: str
    name: str
    description: str
    content: str
    version: int = 1
    is_active: bool = True


DEFAULT_PROMPT_TEMPLATES: tuple[DefaultPromptTemplate, ...] = (
    DefaultPromptTemplate(
        type="chat",
        name="Default Chat System Prompt",
        description="Base system behavior for chat responses grounded in workspace data.",
        content="You are Timebot. Use only uploaded and processed Timebot documents and persisted intelligence. If not found, say so.",
    ),
    DefaultPromptTemplate(
        type="retrieval",
        name="Default Retrieval Prompt",
        description="Guidance for retrieval context assembly used in chat and reports.",
        content="Retrieve timeline events, summaries, relationships, and excerpts.",
    ),
    DefaultPromptTemplate(
        type="report",
        name="Default Report Prompt",
        description="Guidance for report generation grounded in retrieved sources.",
        content="Generate a markdown report grounded in sources.",
    ),
    DefaultPromptTemplate(
        type="timeline_extraction",
        name="Default Timeline Extraction Prompt",
        description="Timeline extraction prompt used by AI document analyzer.",
        content=(
            "Extract structured timeline events from this document. "
            "Return factual events only, include date certainty, and omit speculation."
        ),
    ),
    DefaultPromptTemplate(
        type="relationship_detection",
        name="Default Relationship Detection Prompt",
        description="Relationship detection weighting guidance for follow-up scoring.",
        content=(
            "Prefer relationships where documents reference common entities, shared "
            "dates, and complementary evidence that supports a review connection."
        ),
    ),
)
