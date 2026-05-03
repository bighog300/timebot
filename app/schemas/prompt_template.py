from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class PromptTemplateBase(BaseModel):
    type: str = Field(pattern="^(chat|retrieval|report|timeline_extraction|relationship_detection)$")
    name: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1)
    version: int = Field(ge=1, default=1)
    is_active: bool = False
    provider: str = Field(pattern="^(openai|gemini)$", default="openai")
    model: str = Field(min_length=1, max_length=120, default="gpt-4o-mini")
    temperature: float = Field(ge=0, le=2, default=0.2)
    max_tokens: int = Field(ge=1, le=8192, default=800)
    top_p: float = Field(ge=0, le=1, default=1.0)
    fallback_enabled: bool = False
    fallback_provider: str | None = Field(default=None, pattern="^(openai|gemini)$")
    fallback_model: str | None = Field(default=None, min_length=1, max_length=120)
    enabled: bool = True
    is_default: bool = False

    @field_validator("content")
    @classmethod
    def content_must_not_be_whitespace_only(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("String should have at least 1 non-whitespace character")
        return value


class PromptTemplateCreate(PromptTemplateBase):
    @model_validator(mode="after")
    def validate_fallback(self):
        if self.fallback_enabled and (not self.fallback_provider or not self.fallback_model):
            raise ValueError("fallback_provider and fallback_model are required when fallback_enabled is true")
        return self



class PromptTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    content: str | None = Field(default=None, min_length=1)
    version: int | None = Field(default=None, ge=1)
    is_active: bool | None = None
    provider: str | None = Field(default=None, pattern="^(openai|gemini)$")
    model: str | None = Field(default=None, min_length=1, max_length=120)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, ge=1, le=8192)
    top_p: float | None = Field(default=None, ge=0, le=1)
    enabled: bool | None = None
    is_default: bool | None = None
    fallback_enabled: bool | None = None
    fallback_provider: str | None = Field(default=None, pattern="^(openai|gemini)$")
    fallback_model: str | None = Field(default=None, min_length=1, max_length=120)

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
    provider: str = Field(pattern="^(openai|gemini)$", default="openai")
    model: str = Field(min_length=1, max_length=120, default="gpt-4o-mini")
    temperature: float = Field(ge=0, le=2, default=0.2)
    max_tokens: int = Field(ge=1, le=8192, default=800)
    top_p: float = Field(ge=0, le=1, default=1.0)
    fallback_enabled: bool = False
    fallback_provider: str | None = Field(default=None, pattern="^(openai|gemini)$")
    fallback_model: str | None = Field(default=None, min_length=1, max_length=120)


class PromptTemplateTestResponse(BaseModel):
    preview: str
    latency_ms: float | None = None
    usage_tokens: int | None = None
    fallback_used: bool = False
    provider_used: str
    model_used: str
    primary_error: str | None = None
