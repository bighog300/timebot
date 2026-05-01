from __future__ import annotations

import re

_MAX_LEN = 240
_SENSITIVE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{10,}"),
    re.compile(r"api[_-]?key\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"authorization\s*[:=]\s*\S+", re.IGNORECASE),
    re.compile(r"bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
]


def sanitize_processing_error(message: str | None) -> str | None:
    if not message:
        return None
    trimmed = " ".join(str(message).split())
    for pattern in _SENSITIVE_PATTERNS:
        trimmed = pattern.sub("[redacted]", trimmed)
    if len(trimmed) > _MAX_LEN:
        return "Processing failed due to an internal error."
    lowered = trimmed.lower()
    if any(token in lowered for token in ("summary", "document text", "raw_text", "snippet:")):
        return "Processing failed due to an internal error."
    return trimmed
