from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.v1.admin import _get_or_create_chatbot_settings
from app.config import settings
from app.services.prompt_templates import get_active_prompt_content
from app.models.chat import GeneratedReport
from app.models.user import User
from app.services.chat_retrieval import retrieve_chat_context
from app.services.openai_client import APIError, openai_client_service

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportRequest(BaseModel):
    title: str
    prompt: str
    document_ids: list[str] = []
    include_timeline: bool = True
    include_full_text: bool = False


@router.post("")
def create_report(payload: ReportRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    bot_settings = _get_or_create_chatbot_settings(db)
    if not openai_client_service.enabled:
        raise HTTPException(status_code=503, detail="Report AI is unavailable: OPENAI_API_KEY is not configured.")
    context = retrieve_chat_context(
        db=db,
        query=payload.prompt,
        user_id=user.id,
        document_ids=payload.document_ids,
        include_timeline=payload.include_timeline,
        include_full_text=payload.include_full_text and bot_settings.allow_full_text_retrieval,
        max_documents=bot_settings.max_documents,
    )
    prompt = (
        f"{get_active_prompt_content(db, "report", bot_settings.report_prompt)}\n\nTemplate:\n{bot_settings.default_report_template}\n\n"
        f"User request:\n{payload.prompt}\n\n"
        f"Context:\n{context}\n\n"
        "Ground strictly in context and cite sources."
    )
    try:
        response = openai_client_service.client.chat.completions.create(
            model=bot_settings.model,
            temperature=bot_settings.temperature,
            max_tokens=bot_settings.max_tokens,
            messages=[
                {"role": "system", "content": get_active_prompt_content(db, "chat", bot_settings.system_prompt)},
                {"role": "user", "content": prompt},
            ],
        )
    except APIError as exc:
        raise HTTPException(status_code=503, detail=f"Report AI request failed: {exc}") from exc
    content = (response.choices[0].message.content or "").strip() or f"# {payload.title}\n\nInsufficient evidence in accessible documents."
    report = GeneratedReport(
        title=payload.title,
        prompt=payload.prompt,
        content_markdown=content,
        source_document_ids=payload.document_ids,
        source_refs=context["source_refs"],
        created_by_id=user.id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    report_dir = Path(settings.effective_artifact_dir) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    file_path = report_dir / f"{report.id}.md"
    file_path.write_text(content, encoding="utf-8")
    report.file_path = str(file_path)
    db.add(report)
    db.commit()
    return {"id": str(report.id), "title": report.title, "content_markdown": report.content_markdown, "source_refs": report.source_refs, "download_url": f"/api/v1/reports/{report.id}/download"}


@router.get("")
def list_reports(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(GeneratedReport).filter(GeneratedReport.created_by_id == user.id).order_by(GeneratedReport.created_at.desc()).all()


@router.get("/{report_id}")
def get_report(report_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(GeneratedReport).filter(GeneratedReport.id == report_id, GeneratedReport.created_by_id == user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
def download_report(report_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = db.query(GeneratedReport).filter(GeneratedReport.id == report_id, GeneratedReport.created_by_id == user.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report_dir = Path(settings.effective_artifact_dir) / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c for c in report.title if c.isalnum() or c in (" ", "-", "_")).strip() or "report"
    safe_name = safe_name.replace(" ", "_")
    target_path = Path(report.file_path) if report.file_path else (report_dir / f"{report.id}.md")
    if not target_path.exists():
        if not report.content_markdown:
            raise HTTPException(status_code=404, detail="Report file unavailable")
        target_path.write_text(report.content_markdown, encoding="utf-8")
        if not report.file_path:
            report.file_path = str(target_path)
            db.add(report)
            db.commit()
    return FileResponse(str(target_path), media_type="text/markdown", filename=f"{safe_name}.md")
