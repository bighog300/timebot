import uuid

from app.crud import source_mapping as source_mapping_crud
from app.models.source_mapping import ActiveSourceMapping, SourceProfile
from app.services.crawler.decision import CrawlDecisionEngine


class StubFetcher:
    def __init__(self, pages):
        self.pages = pages

    def fetch(self, url: str):
        data = self.pages.get(url)
        if not data:
            from app.services.crawler.types import FetchResult

            return FetchResult(ok=False, status_code=404, content_type="text/html")
        from app.services.crawler.types import FetchResult

        return FetchResult(ok=True, status_code=200, content_type="text/html", text=data)


def _seed_source_and_mapping(db, source_id: str = "crawl-news"):
    profile = SourceProfile(id=uuid.uuid4(), source_id=source_id, profile_name="crawl", status="ready")
    db.add(profile)
    db.flush()

    compiled_mapping = {
        "source_id": source_id,
        "max_depth": 2,
        "rules": [
            {"id": "exclude-private", "pattern": "*private*", "exclude": True},
            {"id": "article", "pattern": "https://example.com/*", "include": True, "follow": True, "extract": True, "seed_url": "https://example.com/start"},
        ],
    }
    active = ActiveSourceMapping(
        source_id=source_id,
        mapping_draft_id=uuid.uuid4(),
        compiled_mapping=compiled_mapping,
        activated_by="admin@example.com",
    )
    db.add(active)
    db.commit()
    db.refresh(active)
    return profile, active


def test_decision_engine_precedence_and_determinism():
    engine = CrawlDecisionEngine(
        {
            "rules": [
                {"id": "exclude", "pattern": "*blocked*", "exclude": True},
                {"id": "include", "pattern": "https://example.com/*", "include": True, "follow": True, "extract": True},
                {"id": "later", "pattern": "https://example.com/path*", "include": False},
            ]
        }
    )

    blocked = engine.evaluate("https://example.com/blocked/page")
    assert blocked.exclude is True
    assert blocked.include is False
    assert blocked.matched_rule_id == "exclude"

    allowed_one = engine.evaluate("https://example.com/path/a")
    allowed_two = engine.evaluate("https://example.com/path/a")
    assert allowed_one.include is True
    assert allowed_one.matched_rule_id == "include"
    assert allowed_two.matched_rule_id == "include"


def test_crawl_run_executes_and_applies_rules(client, db, monkeypatch):
    _seed_source_and_mapping(db)

    pages = {
        "https://example.com/start": '<a href="/article-1">One</a><a href="/private/secret">Hidden</a><a href="/article-1">Dup</a>',
        "https://example.com/article-1": '<a href="/article-2">Two</a>',
        "https://example.com/article-2": "done",
    }
    from app.api.v1 import sources as sources_api

    monkeypatch.setattr(sources_api.crawl_runner, "fetcher", StubFetcher(pages))

    start = client.post("/api/sources/crawl-news/crawl-runs")
    assert start.status_code == 200
    run_payload = start.json()
    assert run_payload["status"] == "completed"
    assert run_payload["stats_json"]["pages_fetched"] >= 2

    run_id = run_payload["id"]
    detail = client.get(f"/api/sources/crawl-news/crawl-runs/{run_id}")
    assert detail.status_code == 200
    pages = detail.json()["pages"]

    fetched = [p for p in pages if p["status"] == "fetched"]
    skipped = [p for p in pages if p["status"] == "skipped"]
    assert fetched
    assert any("private" in p["url"] for p in skipped)

    # Duplicate URL from seed page should not be processed twice.
    normalized = [p["normalized_url"] for p in pages]
    assert len(normalized) == len(set(normalized))


def test_crawl_fails_without_active_mapping(client, db):
    profile = SourceProfile(id=uuid.uuid4(), source_id="no-active", profile_name="x", status="ready")
    db.add(profile)
    db.commit()

    resp = client.post("/api/sources/no-active/crawl-runs")
    assert resp.status_code == 409


def test_cancel_crawl_requires_admin_and_can_cancel_pending(client, db):
    _profile, active = _seed_source_and_mapping(db, source_id="cancelable")
    run = source_mapping_crud.create_crawl_run(
        db,
        source_id="cancelable",
        active_mapping_id=active.id,
        created_by="admin@example.com",
    )
    db.commit()

    cancel_resp = client.post(f"/api/sources/cancelable/crawl-runs/{run.id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    from app.api.deps import get_current_user
    from app.main import app

    def non_admin_user():
        class _U:
            email = "non-admin@example.com"
            is_admin = False

        return _U()

    app.dependency_overrides[get_current_user] = non_admin_user
    forbidden = client.post("/api/sources/cancelable/crawl-runs")
    assert forbidden.status_code == 403
    app.dependency_overrides.clear()
