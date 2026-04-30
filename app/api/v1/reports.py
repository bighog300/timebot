from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.config import settings
from app.models.chat import GeneratedReport
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportRequest(BaseModel):
    title: str
    prompt: str
    document_ids: list[str] = []


@router.post("")
def create_report(payload: ReportRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    content = f"# {payload.title}\n\n{payload.prompt}\n\n## Sources\n- Generated from Timebot internal documents only."
    report = GeneratedReport(
        title=payload.title,
        prompt=payload.prompt,
        content_markdown=content,
        source_document_ids=payload.document_ids,
        source_refs=[],
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
    if not report or not report.file_path:
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(report.file_path, media_type="text/markdown", filename=f"{report.title}.md")
