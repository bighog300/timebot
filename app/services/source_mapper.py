from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud import source_mapping as source_mapping_crud
from app.models.source_mapping import MappingDraft, MappingRule, UrlFamily


class SourceMapperService:
    @staticmethod
    def infer_rule_from_family(family: UrlFamily, *, source_id: str, rule_order: int, draft_id: UUID) -> MappingRule:
        suggestion = family.suggestion or {}
        return MappingRule(
            draft_id=draft_id,
            source_id=source_id,
            rule_order=rule_order,
            family_key=family.family_key,
            sample_url=family.sample_url,
            selector_suggestion=suggestion.get("selector") or family.locator_hint,
            parse_suggestion=suggestion.get("parse"),
            transform_suggestion=suggestion.get("transform"),
            enabled=True,
        )

    @staticmethod
    def _ordered_families(profile_families: list[UrlFamily]) -> list[UrlFamily]:
        return sorted(profile_families, key=lambda f: (f.family_order, f.family_key, str(f.id)))

    def generate_draft_from_profile(self, db: Session, *, source_id: str, profile_id: UUID) -> MappingDraft:
        profile = source_mapping_crud.get_profile_for_source(db, source_id, profile_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source profile not found for source")

        ordered_families = self._ordered_families(list(profile.url_families))
        draft = source_mapping_crud.create_mapping_draft(db, source_id=source_id, profile_id=profile.id)
        rules = [
            self.infer_rule_from_family(family, source_id=source_id, rule_order=index, draft_id=draft.id)
            for index, family in enumerate(ordered_families)
        ]
        source_mapping_crud.create_mapping_rules(db, rules)

        db.commit()
        return source_mapping_crud.get_source_draft(db, source_id, draft.id)

    def patch_rule(self, db: Session, *, source_id: str, draft_id: UUID, rule_id: UUID, patch: dict) -> MappingRule:
        rule = source_mapping_crud.get_draft_rule(db, source_id, draft_id, rule_id)
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

        allowed = {"selector_override", "parse_override", "transform_override", "notes", "enabled"}
        for field, value in patch.items():
            if field in allowed:
                setattr(rule, field, value)

        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    def bulk_patch_rules(self, db: Session, *, source_id: str, draft_id: UUID, patches: list[dict]) -> MappingDraft:
        for patch in patches:
            self.patch_rule(
                db,
                source_id=source_id,
                draft_id=draft_id,
                rule_id=UUID(str(patch["rule_id"])),
                patch=patch,
            )
        return self.get_draft_or_404(db, source_id=source_id, draft_id=draft_id)

    def approve_draft(self, db: Session, *, source_id: str, draft_id: UUID, approved_by: str | None) -> MappingDraft:
        draft = self.get_draft_or_404(db, source_id=source_id, draft_id=draft_id)
        draft.status = "approved"
        draft.approved_at = datetime.now(timezone.utc)
        draft.approved_by = approved_by
        db.add(draft)
        db.commit()
        return self.get_draft_or_404(db, source_id=source_id, draft_id=draft_id)

    @staticmethod
    def _resolve_value(rule: MappingRule, override_name: str, suggestion_name: str):
        override_value = getattr(rule, override_name)
        if override_value is not None:
            return override_value
        return getattr(rule, suggestion_name)

    def compile_active_mapping(self, draft: MappingDraft) -> dict:
        ordered_rules = sorted(draft.rules, key=lambda r: (r.rule_order, r.family_key, str(r.id)))
        compiled_rules = []
        for rule in ordered_rules:
            if not rule.enabled:
                continue
            compiled_rules.append(
                {
                    "family_key": rule.family_key,
                    "sample_url": rule.sample_url,
                    "selector": self._resolve_value(rule, "selector_override", "selector_suggestion"),
                    "parse": self._resolve_value(rule, "parse_override", "parse_suggestion"),
                    "transform": self._resolve_value(rule, "transform_override", "transform_suggestion"),
                }
            )

        return {
            "source_id": draft.source_id,
            "draft_id": str(draft.id),
            "compiled_at": datetime.now(timezone.utc).isoformat(),
            "rules": compiled_rules,
        }

    def activate_draft(self, db: Session, *, source_id: str, draft_id: UUID, activated_by: str | None):
        draft = self.get_draft_or_404(db, source_id=source_id, draft_id=draft_id)
        if draft.status != "approved":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Draft must be approved before activation")

        compiled = self.compile_active_mapping(draft)
        active = source_mapping_crud.upsert_active_mapping(
            db,
            source_id=source_id,
            draft_id=draft.id,
            compiled_mapping=compiled,
            activated_by=activated_by,
        )
        db.commit()
        db.refresh(active)
        return active

    def get_draft_or_404(self, db: Session, *, source_id: str, draft_id: UUID) -> MappingDraft:
        draft = source_mapping_crud.get_source_draft(db, source_id, draft_id)
        if not draft:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
        return draft


source_mapper_service = SourceMapperService()
