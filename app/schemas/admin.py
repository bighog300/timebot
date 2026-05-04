from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, StrictBool


class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUsersPageResponse(BaseModel):
    items: list[AdminUserResponse]
    total_count: int
    limit: int
    offset: int


class AdminRoleUpdateRequest(BaseModel):
    role: str = Field(pattern="^(viewer|editor|admin)$")


class AdminAuditEventResponse(BaseModel):
    id: UUID
    actor_id: UUID | None
    actor_email: str | None
    entity_type: str
    entity_id: str
    action: str
    details: dict
    created_at: datetime


class AdminAuditPageResponse(BaseModel):
    items: list[AdminAuditEventResponse]
    total_count: int
    limit: int
    offset: int


class AdminMetricsResponse(BaseModel):
    total_users: int
    total_documents: int
    documents_processed: int
    documents_failed: int
    pending_review_items: int
    open_action_items: int
    pending_relationship_reviews: int


class AdminProcessingSummaryResponse(BaseModel):
    pending: int
    processing: int
    completed: int
    failed: int
    recently_failed: int


class ProcessingEventResponse(BaseModel):
    id: UUID
    document_id: UUID
    user_id: UUID | None
    stage: str
    event_type: str
    status: str
    message: str
    severity: str
    duration_ms: int | None
    provider: str | None
    model: str | None
    ai_call_count: int | None
    parse_retry_used: str | None
    error_type: str | None
    safe_metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminSubscriptionResponse(BaseModel):
    user_id: UUID
    email: str
    subscription_id: UUID
    plan_slug: str
    plan_name: str
    status: str
    cancel_at_period_end: bool
    usage_credits: dict
    limit_overrides: dict


class AdminUsageSummaryResponse(BaseModel):
    user_id: UUID
    window_start: datetime
    window_end: datetime
    usage: dict[str, int]


class AdminPlanUpdateRequest(BaseModel):
    plan_slug: str
    subscription_status: str | None = None
    plan_started_at: datetime | None = None
    plan_expires_at: datetime | None = None


class AdminPlanResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    price_monthly_cents: int
    currency: str
    limits_json: dict[str, int | float | None]
    features_json: dict[str, bool]
    is_active: bool

    model_config = {"from_attributes": True}


class AdminPlanPatchRequest(BaseModel):
    name: str | None = None
    price_monthly_cents: int | None = Field(default=None, ge=0)
    limits_json: dict[str, int | float | None] | None = None
    features_json: dict[str, StrictBool] | None = None
    is_active: bool | None = None


class AdminUsageOverrideRequest(BaseModel):
    usage_credits: dict[str, int] = Field(default_factory=dict)
    limit_overrides: dict[str, int | None] = Field(default_factory=dict)


class AdminCancelDowngradeRequest(BaseModel):
    downgrade_to_plan_slug: str = "free"


class AdminSystemStatusFeaturesResponse(BaseModel):
    insights_enabled: bool
    category_intelligence_enabled: bool
    relationship_detection_enabled: bool


class AdminSystemStatusResponse(BaseModel):
    auth_mode: str
    google_auth_enabled: bool
    billing_configured: bool
    stripe_configured: bool
    stripe_prices_configured: bool
    environment: str
    limits_configured: bool
    features: AdminSystemStatusFeaturesResponse


class LlmModelOptionResponse(BaseModel):
    id: str
    name: str


class LlmProviderCatalogResponse(BaseModel):
    id: str
    name: str
    configured: bool
    webhook_configured: bool = False
    models: list[LlmModelOptionResponse]


class AdminLlmModelsResponse(BaseModel):
    providers: list[LlmProviderCatalogResponse]


class SystemComponentStatus(BaseModel):
    status: str
    detail: str | None = None


class AdminSystemHealthResponse(BaseModel):
    overall_status: str
    database: SystemComponentStatus
    redis: SystemComponentStatus
    celery: SystemComponentStatus
    vector_store: SystemComponentStatus
    llm_providers: dict[str, SystemComponentStatus]
    app: dict[str, str | None]


class AdminSystemJobsResponse(BaseModel):
    queue_length: int
    active_jobs: int
    failed_jobs: int
    recent_completed_jobs: int
    retry_count: int
    last_error_summary: str | None = None


class AdminLlmMetricsResponse(BaseModel):
    total_calls: int
    success_count: int
    error_count: int
    error_rate: float
    provider_breakdown: dict[str, int]
    model_breakdown: dict[str, int]
    fallback_usage: int
    latency_percentiles_ms: dict[str, float | None]
    cost_totals: dict[str, float]


class AdminUserCreateRequest(BaseModel):
    email: str
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: str = Field(default="viewer", pattern="^(viewer|editor|admin)$")
    display_name: str | None = None
    send_invite: bool = False


class AdminDeleteUserRequest(BaseModel):
    confirmation: str


class AdminInviteCreateRequest(BaseModel):
    email: str
    role: str = Field(default="viewer", pattern="^(viewer|editor|admin)$")
    expires_in_days: int = Field(default=7, ge=1, le=30)


class AdminInviteResponse(BaseModel):
    id: UUID
    email: str
    role: str
    expires_at: datetime
    accepted_at: datetime | None
    canceled_at: datetime | None
    created_at: datetime
    status: str
    dev_invite_link: str | None = None

    model_config = {"from_attributes": True}

class EmailProviderConfigResponse(BaseModel):
    provider: str
    enabled: bool
    from_email: str
    from_name: str | None
    reply_to: str | None
    configured: bool
    webhook_configured: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmailProviderConfigPatchRequest(BaseModel):
    enabled: bool | None = None
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None
    api_key: str | None = None
    webhook_secret: str | None = None
    clear_webhook_secret: bool | None = None


class EmailTemplateCreateRequest(BaseModel):
    name: str
    slug: str
    category: str = Field(pattern="^(transactional|campaign|system)$")
    status: str = Field(default="draft", pattern="^(draft|active|archived)$")
    subject: str
    preheader: str | None = None
    html_body: str
    text_body: str | None = None
    variables_json: dict | list = Field(default_factory=dict)


class EmailTemplatePatchRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    category: str | None = Field(default=None, pattern="^(transactional|campaign|system)$")
    status: str | None = Field(default=None, pattern="^(draft|active|archived)$")
    subject: str | None = None
    preheader: str | None = None
    html_body: str | None = None
    text_body: str | None = None
    variables_json: dict | list | None = None


class EmailTemplateResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    category: str
    status: str
    subject: str
    preheader: str | None
    html_body: str
    text_body: str | None
    variables_json: dict | list
    created_by_admin_id: UUID | None
    updated_by_admin_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class EmailCampaignCreateRequest(BaseModel):
    name: str
    template_id: UUID
    audience_type: str
    audience_filters_json: dict | list | None = None
    status: str = Field(default="draft", pattern="^(draft|ready|archived)$")
    subject_override: str | None = None
    preheader_override: str | None = None
    variables_json: dict | list | None = None


class EmailCampaignPatchRequest(BaseModel):
    name: str | None = None
    template_id: UUID | None = None
    audience_type: str | None = None
    audience_filters_json: dict | list | None = None
    status: str | None = Field(default=None, pattern="^(draft|ready|archived)$")
    subject_override: str | None = None
    preheader_override: str | None = None
    variables_json: dict | list | None = None


class EmailCampaignResponse(BaseModel):
    id: UUID
    name: str
    template_id: UUID
    audience_type: str
    audience_filters_json: dict | list | None
    status: str
    subject_override: str | None
    preheader_override: str | None
    variables_json: dict | list | None
    created_by_admin_id: UUID | None
    updated_by_admin_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmailCampaignPreviewRequest(BaseModel):
    variables_json: dict | list | None = None


class EmailCampaignPreviewResponse(BaseModel):
    subject: str
    preheader: str | None
    html_body: str
    text_body: str
    missing_variables: list[str]




class EmailSuppressionCreateRequest(BaseModel):
    email: str
    reason: str = Field(pattern="^(unsubscribe|bounce|complaint|manual)$")
    source: str | None = None


class EmailSuppressionResponse(BaseModel):
    id: UUID
    email: str
    reason: str
    source: str | None
    created_by_admin_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailCampaignRecipientPreviewResponse(BaseModel):
    total_candidates: int
    sendable_count: int
    suppressed_count: int
    invalid_count: int
    duplicate_count: int
    sample_recipients: list[str]
    suppressed_samples: list[str]
    invalid_samples: list[str]


class EmailCampaignSendRequest(BaseModel):
    provider: str | None = Field(default=None, pattern="^(resend|sendgrid)$")
    confirmation_text: str
    variables_json: dict | list | None = None


class EmailCampaignSendResponse(BaseModel):
    total_candidates: int
    sendable_count: int
    sent_count: int
    failed_count: int
    skipped_count: int
    status: str | None = None
    campaign_id: str | None = None
    recipient_count: int | None = None


class EmailCampaignTestSendRequest(BaseModel):
    to_email: str
    provider: str | None = Field(default=None, pattern="^(resend|sendgrid)$")
    variables_json: dict | list | None = None


class AdminEmailTestSendRequest(BaseModel):
    provider: str | None = Field(default=None, pattern="^(resend|sendgrid)$")
    to_email: str
    subject: str | None = None
    html_body: str | None = None
    text_body: str | None = None


class AdminEmailTestSendResponse(BaseModel):
    status: str
    provider: str
    provider_message_id: str | None
    log_id: UUID


class EmailSendLogResponse(BaseModel):
    id: UUID
    provider: str
    recipient_email: str
    from_email: str
    from_name: str | None
    reply_to: str | None
    subject: str
    status: str
    provider_message_id: str | None
    error_message_sanitized: str | None
    created_at: datetime
    sent_at: datetime | None
    failed_at: datetime | None

    model_config = {"from_attributes": True}
