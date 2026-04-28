from dataclasses import dataclass, field


@dataclass
class QueueItem:
    url: str
    depth: int
    parent_url: str | None = None


@dataclass
class FetchResult:
    ok: bool
    status_code: int | None = None
    content_type: str | None = None
    text: str | None = None
    error_type: str | None = None
    error_message: str | None = None


@dataclass
class DecisionResult:
    include: bool
    exclude: bool
    follow_links: bool
    extract_content: bool
    paginate: bool
    matched_rule_id: str | None
    reason_codes: list[str] = field(default_factory=list)
