import uuid

from app.models.source_mapping import MappingDraft, MappingRule, SourceProfile, UrlFamily
from app.services.source_mapper import source_mapper_service


def _seed_profile(db, *, source_id: str = "news"):
    profile = SourceProfile(
        id=uuid.uuid4(),
        source_id=source_id,
        profile_name="primary-profile",
        status="ready",
    )
    db.add(profile)
    db.flush()

    families = [
        UrlFamily(
            id=uuid.uuid4(),
            source_profile_id=profile.id,
            family_key="article",
            sample_url="https://example.com/a/1",
            locator_hint="css:.headline",
            suggestion={"selector": "css:h1", "parse": "text", "transform": "strip"},
            family_order=2,
        ),
        UrlFamily(
            id=uuid.uuid4(),
            source_profile_id=profile.id,
            family_key="listing",
            sample_url="https://example.com/list",
            locator_hint="css:.list-title",
            suggestion={"selector": "css:.title", "parse": "text"},
            family_order=1,
        ),
    ]
    db.add_all(families)
    db.commit()
    db.refresh(profile)
    return profile


def test_inference_and_compiler_use_admin_overrides_deterministically(db):
    profile = _seed_profile(db)
    draft = source_mapper_service.generate_draft_from_profile(db, source_id="news", profile_id=profile.id)

    assert [r.family_key for r in draft.rules] == ["listing", "article"]

    listing_rule = draft.rules[0]
    article_rule = draft.rules[1]

    listing_rule.selector_override = "css:.title-override"
    article_rule.enabled = False

    compiled = source_mapper_service.compile_active_mapping(draft)
    assert [r["family_key"] for r in compiled["rules"]] == ["listing"]
    assert compiled["rules"][0]["selector"] == "css:.title-override"
    assert compiled["rules"][0]["parse"] == "text"


def test_generate_endpoint_edit_approve_activate_flow(client, db):
    profile = _seed_profile(db, source_id="blog")

    create_resp = client.post(f"/api/sources/blog/mapping-drafts/from-profile/{profile.id}")
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["status"] == "draft"
    assert len(created["rules"]) == 2

    draft_id = created["id"]
    rule_id = created["rules"][0]["id"]

    patch_resp = client.patch(
        f"/api/sources/blog/mapping-drafts/{draft_id}/rules/{rule_id}",
        json={"selector_override": "css:.admin", "notes": "admin reviewed"},
    )
    assert patch_resp.status_code == 200
    patched_rule = patch_resp.json()
    assert patched_rule["selector_suggestion"] is not None
    assert patched_rule["selector_override"] == "css:.admin"

    not_approved_activate = client.post(f"/api/sources/blog/mapping-drafts/{draft_id}/activate")
    assert not_approved_activate.status_code == 409

    approve_resp = client.post(f"/api/sources/blog/mapping-drafts/{draft_id}/approve")
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    activate_resp = client.post(f"/api/sources/blog/mapping-drafts/{draft_id}/activate")
    assert activate_resp.status_code == 200
    activated = activate_resp.json()
    assert activated["mapping_draft_id"] == draft_id
    compiled_rules = activated["compiled_mapping"]["rules"]
    assert compiled_rules[0]["selector"] == "css:.admin"

    active_resp = client.get("/api/sources/blog/mapping-active")
    assert active_resp.status_code == 200
    assert active_resp.json()["mapping_draft_id"] == draft_id


def test_draft_generation_requires_profile_from_same_source(client, db):
    profile = _seed_profile(db, source_id="science")

    resp = client.post(f"/api/sources/sports/mapping-drafts/from-profile/{profile.id}")
    assert resp.status_code == 404


def test_bulk_patch_endpoint_and_draft_listing(client, db):
    profile = _seed_profile(db, source_id="finance")
    create_resp = client.post(f"/api/sources/finance/mapping-drafts/from-profile/{profile.id}")
    draft_id = create_resp.json()["id"]
    rules = create_resp.json()["rules"]

    bulk_resp = client.patch(
        f"/api/sources/finance/mapping-drafts/{draft_id}/rules",
        json={
            "patches": [
                {"rule_id": rules[0]["id"], "selector_override": "css:.finance-1"},
                {"rule_id": rules[1]["id"], "enabled": False},
            ]
        },
    )
    assert bulk_resp.status_code == 200
    payload = bulk_resp.json()
    assert payload["rules"][0]["selector_override"] == "css:.finance-1"
    assert payload["rules"][1]["enabled"] is False

    list_resp = client.get("/api/sources/finance/mapping-drafts")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
