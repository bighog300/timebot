from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class ChatbotSettingsPayload(BaseModel):
    system_prompt: str
    retrieval_prompt: str
    report_prompt: str
    citation_prompt: str
    default_report_template: str
    model: str
    temperature: float
    max_tokens: int
    max_documents: int
    allow_full_text_retrieval: bool
    prompt_daily_cost_threshold_usd: float | None = None
    prompt_monthly_cost_threshold_usd: float | None = None
    prompt_user_cost_threshold_usd: float | None = None
    prompt_workspace_cost_threshold_usd: float | None = None


class ChatbotSettingsResponse(ChatbotSettingsPayload):
    id: UUID
    updated_by_id: UUID | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}
