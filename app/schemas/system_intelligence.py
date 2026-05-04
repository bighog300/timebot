import uuid
from datetime import datetime
from pydantic import BaseModel


class SystemIntelligenceDocumentCreate(BaseModel):
    source_type: str
    title: str
    description: str | None = None
    category: str | None = None
    jurisdiction: str | None = None
    storage_uri: str | None = None
    mime_type: str | None = None
    content_hash: str | None = None
    metadata_json: dict | None = None


class SystemIntelligenceDocumentPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    jurisdiction: str | None = None
    status: str | None = None
    storage_uri: str | None = None
    mime_type: str | None = None
    content_hash: str | None = None
    metadata_json: dict | None = None


class SystemIntelligenceDocumentResponse(BaseModel):
    id: uuid.UUID
    source_type: str
    status: str
    title: str
    description: str | None
    category: str | None
    jurisdiction: str | None
    storage_uri: str | None
    mime_type: str | None
    original_filename: str | None = None
    size_bytes: int | None = None
    content_hash: str | None
    extraction_status: str
    extraction_error: str | None = None
    index_status: str
    index_error: str | None = None
    version: int
    metadata_json: dict | None
    indexed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class SystemIntelligenceSubmissionCreate(BaseModel):
    workspace_id: uuid.UUID | None = None
    source_document_id: uuid.UUID | None = None
    source_drive_file_id: str | None = None
    title: str
    suggested_category: str | None = None
    suggested_jurisdiction: str | None = None
    reason: str | None = None


class SystemIntelligenceSubmissionModeration(BaseModel):
    admin_notes: str | None = None


class SystemIntelligenceSubmissionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    workspace_id: uuid.UUID | None
    source_document_id: uuid.UUID | None
    source_drive_file_id: str | None
    title: str
    suggested_category: str | None
    suggested_jurisdiction: str | None
    reason: str | None
    status: str
    admin_notes: str | None
    reviewed_by_admin_id: uuid.UUID | None
    resulting_system_document_id: uuid.UUID | None
    created_at: datetime

    class Config:
        from_attributes = True


class SystemIntelligenceWebReferenceCreate(BaseModel):
    title: str
    url: str
    canonical_url: str | None = None
    source_domain: str | None = None
    jurisdiction: str | None = None
    court_or_institution: str | None = None
    document_type: str | None = None
    legal_area: str | None = None
    summary: str | None = None
    key_points_json: list | dict | None = None
    citation_text: str | None = None
    content_hash: str | None = None


class SystemIntelligenceWebReferencePatch(BaseModel):
    title: str | None = None
    url: str | None = None
    canonical_url: str | None = None
    source_domain: str | None = None
    jurisdiction: str | None = None
    court_or_institution: str | None = None
    document_type: str | None = None
    legal_area: str | None = None
    summary: str | None = None
    key_points_json: list | dict | None = None
    citation_text: str | None = None
    content_hash: str | None = None
    status: str | None = None


class SystemIntelligenceWebReferenceResponse(BaseModel):
    id: uuid.UUID
    title: str
    url: str
    status: str
    summary: str | None
    source_domain: str | None
    jurisdiction: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class SystemIntelligenceAuditLogResponse(BaseModel):
    id: uuid.UUID
    actor: str
    action: str
    target_type: str
    target_id: str
    metadata_json: dict | None
    created_at: datetime

    class Config:
        from_attributes = True
