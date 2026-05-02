from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class PromptTemplateBase(BaseModel):
    type: str = Field(pattern="^(chat|retrieval|report|timeline_extraction|relationship_detection)$")
    name: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1)
    version: int = Field(ge=1, default=1)
    is_active: bool = False

    @field_validator("content")
    @classmethod
    def content_must_not_be_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("String should have at least 1 non-whitespace character")
        return value


class PromptTemplateCreate(PromptTemplateBase):
    pass


class PromptTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    content: str | None = Field(default=None, min_length=1)
    version: int | None = Field(default=None, ge=1)
    is_active: bool | None = None

    @field_validator("content")
    @classmethod
    def content_must_not_be_whitespace_only(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("String should have at least 1 non-whitespace character")
        return value


class PromptTemplateResponse(PromptTemplateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptTemplateTestRequest(BaseModel):
    type: str = Field(pattern="^(chat|retrieval|report|timeline_extraction|relationship_detection)$")
    content: str = Field(min_length=1)
    sample_context: str = Field(min_length=1)


class PromptTemplateTestResponse(BaseModel):
    preview: str
