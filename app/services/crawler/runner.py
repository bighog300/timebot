import hashlib
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.orm import Session

from app.crud import source_mapping as source_mapping_crud
from app.services.crawler.decision import CrawlDecisionEngine
from app.services.crawler.fetcher import HttpFetcher
from app.services.crawler.parser import LinkParser
from app.services.crawler.queue import CrawlQueue
from app.services.crawler.types import QueueItem


class CrawlRunner:
    def __init__(self, fetcher: HttpFetcher | None = None, parser: LinkParser | None = None):
        self.fetcher = fetcher or HttpFetcher()
        self.parser = parser or LinkParser()

    @staticmethod
    def normalize_url(url: str) -> str:
        parsed = urlparse(url)
        query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
        normalized = parsed._replace(fragment="", query=query)
        return urlunparse(normalized)

    @staticmethod
    def _seed_urls(compiled_mapping: dict) -> list[str]:
        rules = compiled_mapping.get("rules") or []
        seeds = [r.get("seed_url") or r.get("sample_url") for r in rules if (r.get("seed_url") or r.get("sample_url"))]
        return sorted(dict.fromkeys(seeds))

    @staticmethod
    def _increment_stat(run, key: str, amount: int = 1):
        stats = dict(run.stats_json or {})
        stats[key] = int(stats.get(key, 0)) + amount
        run.stats_json = stats

    def execute(self, db: Session, *, source_id: str, run_id):
        run = source_mapping_crud.get_crawl_run_shallow(db, source_id, run_id)
        if not run:
            return None

        active = source_mapping_crud.get_active_mapping(db, source_id)
        engine = CrawlDecisionEngine(active.compiled_mapping)
        max_depth = int((active.compiled_mapping or {}).get("max_depth", 2))

        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        run.stats_json = {"pages_discovered": 0, "pages_fetched": 0, "pages_skipped": 0, "pages_failed": 0}
        db.add(run)
        db.commit()

        queue = CrawlQueue()
        for seed in self._seed_urls(active.compiled_mapping):
            queue.enqueue(QueueItem(url=seed, depth=0), self.normalize_url(seed))

        while not queue.empty():
            db.refresh(run)
            if run.status == "cancelled":
                run.completed_at = datetime.now(timezone.utc)
                db.add(run)
                db.commit()
                return run

            item = queue.dequeue()
            if item is None:
                break

            normalized = self.normalize_url(item.url)
            self._increment_stat(run, "pages_discovered")

            decision = engine.evaluate(normalized)
            if decision.exclude or not decision.include:
                page = source_mapping_crud.create_crawl_page(
                    db,
                    crawl_run_id=run.id,
                    url=item.url,
                    normalized_url=normalized,
                    depth=item.depth,
                    parent_url=item.parent_url,
                    status="skipped",
                )
                source_mapping_crud.create_crawl_decision(
                    db,
                    crawl_page_id=page.id,
                    decision_type="exclude" if decision.exclude else "skip",
                    matched_rule_id=decision.matched_rule_id,
                    reason_codes_json=decision.reason_codes,
                )
                self._increment_stat(run, "pages_skipped")
                db.add(run)
                db.commit()
                continue

            fetch_result = self.fetcher.fetch(item.url)
            if not fetch_result.ok:
                page = source_mapping_crud.create_crawl_page(
                    db,
                    crawl_run_id=run.id,
                    url=item.url,
                    normalized_url=normalized,
                    depth=item.depth,
                    parent_url=item.parent_url,
                    status="failed",
                    http_status=fetch_result.status_code,
                    content_type=fetch_result.content_type,
                )
                source_mapping_crud.create_crawl_decision(
                    db,
                    crawl_page_id=page.id,
                    decision_type="include",
                    matched_rule_id=decision.matched_rule_id,
                    reason_codes_json=decision.reason_codes,
                )
                if fetch_result.error_type:
                    source_mapping_crud.create_crawl_error(
                        db,
                        crawl_page_id=page.id,
                        error_type=fetch_result.error_type,
                        error_message=fetch_result.error_message or "fetch error",
                    )
                self._increment_stat(run, "pages_failed")
                db.add(run)
                db.commit()
                continue

            body = fetch_result.text or ""
            page = source_mapping_crud.create_crawl_page(
                db,
                crawl_run_id=run.id,
                url=item.url,
                normalized_url=normalized,
                depth=item.depth,
                parent_url=item.parent_url,
                status="fetched",
                http_status=fetch_result.status_code,
                content_type=fetch_result.content_type,
                content_hash=hashlib.sha256(body.encode("utf-8")).hexdigest(),
                extracted_text=body if decision.extract_content else None,
            )
            source_mapping_crud.create_crawl_decision(
                db,
                crawl_page_id=page.id,
                decision_type="include",
                matched_rule_id=decision.matched_rule_id,
                reason_codes_json=decision.reason_codes,
            )
            source_mapping_crud.create_crawl_decision(
                db,
                crawl_page_id=page.id,
                decision_type="extract" if decision.extract_content else "skip",
                matched_rule_id=decision.matched_rule_id,
                reason_codes_json=["extract_enabled" if decision.extract_content else "extract_disabled"],
            )

            self._increment_stat(run, "pages_fetched")

            if decision.follow_links and item.depth < max_depth and body:
                links = self.parser.extract_links(body, base_url=item.url)
                for link in links:
                    normalized_link = self.normalize_url(link)
                    queue.enqueue(QueueItem(url=link, depth=item.depth + 1, parent_url=item.url), normalized_link)

            db.add(run)
            db.commit()

        run.status = "completed"
        run.completed_at = datetime.now(timezone.utc)
        db.add(run)
        db.commit()
        return run


crawl_runner = CrawlRunner()
