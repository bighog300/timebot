from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.divorce import DivorceCommunication, DivorceReport, DivorceTimelineItem
from app.models.intelligence import DocumentActionItem
from app.models.workspace import WorkspaceMember

REPORT_TYPES = {
    "case_overview_report",
    "legal_advisor_summary",
    "psychological_communication_dynamics_report",
    "evidence_timeline_report",
    "task_deadline_report",
    "lawyer_handoff_pack",
}
PRO_REPORT_TYPES = REPORT_TYPES - {"case_overview_report"}

DISCLAIMER = "This report is informational only and is not legal advice, mental health advice, or a substitute for licensed professional review."


def verify_workspace_access(db: Session, workspace_id: str, user_id) -> None:
    member = db.query(WorkspaceMember).filter_by(workspace_id=workspace_id, user_id=user_id).first()
    if not member:
        raise HTTPException(status_code=403, detail="Forbidden")


def _doc_snippet(doc: Document) -> str:
    return (doc.summary or doc.raw_text or "")[:220].strip()


def generate_divorce_report(
    db: Session,
    *,
    workspace_id: str,
    user_id,
    report_type: str,
    title: str | None = None,
    include_task_ids: list[str] | None = None,
    include_timeline_item_ids: list[str] | None = None,
    include_document_ids: list[str] | None = None,
    date_range: dict | None = None,
) -> DivorceReport:
    verify_workspace_access(db, workspace_id, user_id)
    if report_type not in REPORT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported report type")

    q_timeline = db.query(DivorceTimelineItem).filter(
        DivorceTimelineItem.workspace_id == workspace_id,
        DivorceTimelineItem.review_status.in_(["accepted", "edited"]),
        DivorceTimelineItem.include_in_report.is_(True),
    )
    if include_timeline_item_ids:
        q_timeline = q_timeline.filter(DivorceTimelineItem.id.in_(include_timeline_item_ids))
    if date_range and date_range.get("start"):
        q_timeline = q_timeline.filter(DivorceTimelineItem.event_date >= date_range["start"])
    if date_range and date_range.get("end"):
        q_timeline = q_timeline.filter(DivorceTimelineItem.event_date <= date_range["end"])
    timeline = q_timeline.order_by(DivorceTimelineItem.event_date.asc().nulls_last()).all()

    q_tasks = db.query(DocumentActionItem).filter(
        DocumentActionItem.workspace_id == workspace_id,
        DocumentActionItem.status.in_(["suggested", "open", "done", "in_progress"]),
    )
    if include_task_ids:
        q_tasks = q_tasks.filter(DocumentActionItem.id.in_(include_task_ids))
    tasks = q_tasks.order_by(DocumentActionItem.due_date.asc().nulls_last()).all()

    q_docs = db.query(Document).filter(Document.workspace_id == workspace_id)
    if include_document_ids:
        q_docs = q_docs.filter(Document.id.in_(include_document_ids))
    docs = q_docs.order_by(Document.upload_date.desc()).limit(25).all()

    lines = [f"# {title or report_type.replace('_', ' ').title()}", "", "## Facts", ""]
    for ev in timeline[:20]:
        lines.append(f"- [{ev.id}] {ev.event_date or 'Undated'}: {ev.title}.")
    lines.extend(["", "## Inferences", "", "- Based only on accepted timeline items, task states, and linked document summaries."])
    lines.extend(["", "## Risks", "", "- Missing dates, unresolved tasks, and sparse evidence may weaken legal positioning."])
    lines.extend(["", "## Recommended Actions", ""])
    for t in tasks[:12]:
        lines.append(f"- [{t.id}] {t.content} (status: {t.status}{', due: ' + str(t.due_date) if t.due_date else ''}).")
    accepted_comms = db.query(DivorceCommunication).filter(DivorceCommunication.workspace_id == workspace_id, DivorceCommunication.review_status.in_(["accepted","edited"])).order_by(DivorceCommunication.sent_at.desc().nulls_last()).limit(20).all()

    lines.extend(["", "## Evidence References", ""])
    for d in docs[:10]:
        lines.append(f"- [{d.id}] {d.filename}: {_doc_snippet(d)}")

    if accepted_comms:
        lines.extend(["", "## Accepted Communications", ""])
        for c in accepted_comms[:10]:
            lines.append(f"- {c.sent_at or 'Undated'} {c.sender} → {c.recipient or '(unknown)'}: {c.subject or '(no subject)'} [{c.tone}/{c.category}]")

    if report_type == "lawyer_handoff_pack":
        lines.extend([
            "",
            "## Matter Summary",
            "- Summary synthesized from accepted records only.",
            "## Parties / Context",
            "- Parties and context should be verified by counsel.",
            "## Key Chronology",
            *[f"- {ev.event_date or 'Undated'} — {ev.title}" for ev in timeline[:12]],
            "## Important Documents",
            *[f"- {d.filename}" for d in docs[:12]],
            "## Open Questions",
            "- What high-impact facts still lack documentary support?",
            "## Tasks / Deadlines",
            *[f"- {t.content}" for t in tasks[:12]],
            "## Risks",
            "- Potential gaps between allegations and documentary support.",
            "## Evidence Gaps",
            "- Identify claims without accepted timeline or document references.",
            "## Suggested Attorney Questions",
            "- Which immediate filings, disclosures, and preservation steps are time-critical?",
        ])

    lines.extend(["", "## Disclaimer", DISCLAIMER])
    content = "\n".join(lines)

    report = DivorceReport(
        workspace_id=workspace_id,
        report_type=report_type,
        title=title or report_type.replace("_", " ").title(),
        status="ready",
        content_markdown=content,
        source_task_ids_json=[str(t.id) for t in tasks],
        source_timeline_item_ids_json=[str(t.id) for t in timeline],
        source_document_ids_json=[str(d.id) for d in docs],
        generated_by_user_id=user_id,
        generated_at=datetime.now(timezone.utc),
        metadata_json={"date_range": date_range or {}, "source_counts": {"tasks": len(tasks), "timeline": len(timeline), "documents": len(docs)}},
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
