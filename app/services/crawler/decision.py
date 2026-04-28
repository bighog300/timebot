import fnmatch
import re

from app.services.crawler.types import DecisionResult


class CrawlDecisionEngine:
    def __init__(self, compiled_mapping: dict):
        self.compiled_mapping = compiled_mapping or {}
        self.rules = list(self.compiled_mapping.get("rules") or [])

    @staticmethod
    def _matches(url: str, rule: dict) -> bool:
        pattern = rule.get("pattern") or rule.get("url_pattern")
        if pattern:
            if pattern.startswith("regex:"):
                return re.search(pattern[len("regex:") :], url) is not None
            return fnmatch.fnmatch(url, pattern)

        sample_url = rule.get("sample_url")
        if sample_url:
            return url.startswith(sample_url)

        return False

    def evaluate(self, url: str) -> DecisionResult:
        for idx, rule in enumerate(self.rules):
            if not self._matches(url, rule):
                continue

            matched_rule_id = str(rule.get("id") or rule.get("family_key") or idx)
            if rule.get("exclude") is True:
                return DecisionResult(
                    include=False,
                    exclude=True,
                    follow_links=False,
                    extract_content=False,
                    paginate=False,
                    matched_rule_id=matched_rule_id,
                    reason_codes=["exclude_rule"],
                )

            include = bool(rule.get("include", True))
            return DecisionResult(
                include=include,
                exclude=False,
                follow_links=bool(rule.get("follow", True)),
                extract_content=bool(rule.get("extract", include)),
                paginate=bool(rule.get("paginate", False)),
                matched_rule_id=matched_rule_id,
                reason_codes=["include_rule" if include else "skip_rule"],
            )

        return DecisionResult(
            include=False,
            exclude=False,
            follow_links=False,
            extract_content=False,
            paginate=False,
            matched_rule_id=None,
            reason_codes=["no_matching_rule"],
        )
