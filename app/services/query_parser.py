import re
from dataclasses import dataclass, field
from typing import Dict, List, Set


STOP_WORDS: Set[str] = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "if",
    "in",
    "into",
    "is",
    "it",
    "no",
    "not",
    "of",
    "on",
    "or",
    "s",
    "such",
    "t",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "was",
    "will",
    "with",
}


@dataclass
class ParsedQuery:
    raw: str
    normalized: str
    terms: List[str]
    phrases: List[str] = field(default_factory=list)
    excluded_terms: List[str] = field(default_factory=list)

    def as_debug(self) -> Dict[str, List[str] | str]:
        return {
            "raw": self.raw,
            "normalized": self.normalized,
            "terms": self.terms,
            "phrases": self.phrases,
            "excluded_terms": self.excluded_terms,
        }


class QueryParser:
    """Deterministic parser that supports quoted phrases and excluded terms."""

    phrase_pattern = re.compile(r'"([^"]+)"')

    def parse(self, query: str) -> ParsedQuery:
        raw = query or ""
        normalized = re.sub(r"\s+", " ", raw).strip()

        phrases = [p.strip().lower() for p in self.phrase_pattern.findall(normalized) if p.strip()]
        stripped = self.phrase_pattern.sub(" ", normalized)

        excluded_terms: List[str] = []
        terms: List[str] = []

        for token in re.findall(r"[\w\-\.]+", stripped.lower()):
            if token.startswith("-") and len(token) > 1:
                cleaned = token[1:]
                if cleaned and cleaned not in STOP_WORDS:
                    excluded_terms.append(cleaned)
                continue

            if token in STOP_WORDS:
                continue
            terms.append(token)

        # Preserve order while deduplicating
        dedup_terms = list(dict.fromkeys(terms))
        dedup_phrases = list(dict.fromkeys(phrases))
        dedup_excluded = list(dict.fromkeys(excluded_terms))

        return ParsedQuery(
            raw=raw,
            normalized=normalized,
            terms=dedup_terms,
            phrases=dedup_phrases,
            excluded_terms=dedup_excluded,
        )


query_parser = QueryParser()
