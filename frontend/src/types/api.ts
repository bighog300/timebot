export interface CategoryInfo {
  id: string;
  name: string;
  color: string;
  icon?: string | null;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  source: string;
  upload_date: string;
  processing_status: string;
  processing_stage?: 'uploading' | 'queued' | 'extracting' | 'analyzing' | 'enriching' | 'embedding' | 'completed' | 'failed';
  processing_progress?: number;
  processing_message?: string | null;
  stage_started_at?: string | null;
  stage_updated_at?: string | null;
  processing_error?: string | null;
  enrichment_status?: "pending" | "complete" | "degraded";
  enrichment_pending?: boolean;
  intelligence_warnings?: string[];
  ai_analysis_degraded?: boolean;
  json_parse_retry_used?: boolean;
  summary?: string | null;
  key_points?: string[] | null;
  entities?: Record<string, unknown> | null;
  action_items?: string[] | null;
  ai_tags: string[];
  user_tags: string[];
  ai_confidence?: number | null;
  review_status?: 'pending' | 'approved' | 'rejected' | 'edited' | null;
  reviewed_at?: string | null;
  reviewed_by?: string | null;
  override_summary?: string | null;
  override_tags?: string[] | null;
  is_favorite: boolean;
  is_archived: boolean;
  user_notes?: string | null;
  page_count?: number | null;
  word_count?: number | null;
  ai_category?: CategoryInfo | null;
  user_category?: CategoryInfo | null;
}

export interface ProcessingEvent {
  id: string;
  document_id: string;
  user_id?: string | null;
  stage: string;
  event_type: string;
  status: string;
  message: string;
  severity: 'info' | 'warning' | 'error';
  duration_ms?: number | null;
  provider?: string | null;
  model?: string | null;
  ai_call_count?: number | null;
  parse_retry_used?: string | null;
  error_type?: string | null;
  safe_metadata: Record<string, unknown>;
  created_at: string;
}

export interface SearchResultItem {
  document: Document;
  relevance: number;
  highlights: string[];
  score_breakdown?: Record<string, unknown>;
}

export interface SearchResponse {
  results: SearchResultItem[];
  total: number;
  query: string;
  page: number;
  pages: number;
}

export interface SemanticSearchResult {
  document: Document;
  similarity_score: number;
  metadata?: Record<string, unknown>;
}

export interface SemanticSearchResponse {
  query: string;
  results: SemanticSearchResult[];
  total: number;
}

export interface QueueStats {
  queued: number;
  processing: number;
  completed: number;
  failed: number;
  total: number;
  pending_review_count: number;
  celery_active?: number | null;
  celery_reserved?: number | null;
}

export interface QueueItem {
  id: string;
  document_id: string;
  task_type: string;
  status: string;
  priority: number;
  attempts: number;
  max_attempts: number;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface TimelineEvent {
  event_id?: string | null;
  title: string;
  description?: string | null;
  date?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  confidence?: number | null;
  signal_strength?: "strong" | "medium" | "weak" | null;
  source_quote?: string | null;
  page_number?: number | null;
  document_id: string;
  document_title: string;
  category?: string | null;
  source?: string | null;
  date_precision?: string | null;
  metadata?: Record<string, unknown> | null;
  is_milestone?: boolean;
  milestone_reason?: string | null;
}

export interface TimelineResponse {
  total_documents: number;
  total_events: number;
  events: TimelineEvent[];
  gaps?: Array<{
    start_date: string;
    end_date: string;
    gap_duration_days: number;
  }> | null;
}

export interface InsightsResponse {
  generated_at: string;
  lookback_days: number;
  volume_trends: Array<Record<string, unknown>>;
  category_distribution: Array<Record<string, unknown>>;
  source_distribution: Record<string, number>;
  action_item_summary: Record<string, unknown>;
  duplicate_clusters: string[][];
  relationship_summary: Record<string, number>;
  recent_activity: Array<Record<string, unknown>>;
}

export interface StructuredInsightDocumentRef {
  document_id: string;
  title?: string | null;
}

export interface StructuredInsightEvidenceRef {
  source?: string | null;
  reference?: string | null;
  quote?: string | null;
}

export interface StructuredInsightsResponse {
  generated_at?: string;
  count?: number;
  insights?: StructuredInsight[] | null;
}

export interface StructuredInsight {
  type: string;
  title: string;
  description: string;
  severity: string;
  related_event_ids?: string[] | null;
  related_document_ids?: string[] | null;
  related_documents?: StructuredInsightDocumentRef[] | null;
  evidence_refs?: StructuredInsightEvidenceRef[] | null;
}

export interface Connection {
  id: string;
  type: 'gmail' | 'gdrive' | 'dropbox' | 'onedrive';
  status: 'connected' | 'disconnected' | 'error' | 'syncing' | 'auth_pending';
  display_name: string;
  email?: string | null;
  external_account_id?: string | null;
  last_sync_date?: string | null;
  last_sync_status?: 'success' | 'failed' | 'partial' | 'in_progress' | null;
  last_error_message?: string | null;
  last_error_at?: string | null;
  sync_progress: number;
  document_count: number;
  total_size: number;
  auto_sync: boolean;
  sync_interval: number;
  is_authenticated: boolean;
  provider_is_configured?: boolean;
  provider_config_error?: string | null;
}

export interface ConnectStartResponse {
  provider: string;
  authorization_url: string;
  state: string;
}

export interface SyncRunResponse {
  message: string;
  files_seen: number;
  documents_added: number;
  documents_updated: number;
  documents_failed: number;
  bytes_synced: number;
  connection: Connection;
}

export interface SyncLog {
  id: string;
  connection_id: string;
  start_time: string;
  end_time?: string | null;
  status: string;
  documents_added: number;
  documents_updated: number;
  documents_failed: number;
  bytes_synced: number;
  error_message?: string | null;
}

export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
  role: "viewer" | "editor" | "admin";
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface DocumentIntelligence {
  document_id: string;
  summary: string | null;
  key_points: string[];
  suggested_category_id: string | null;
  confidence: 'low' | 'medium' | 'high';
  suggested_tags: string[];
  entities: Record<string, unknown>;
  model_name: string | null;
  model_version: string | null;
  model_metadata: Record<string, unknown>;
  category_status: 'suggested' | 'approved' | 'overridden';
  generated_at: string;
  updated_at: string;
}

export interface ReviewItem {
  id: string;
  document_id: string;
  review_type: 'low_confidence' | 'uncategorized' | 'missing_tags' | 'duplicates' | 'action_items' | 'processing_issues';
  status: 'open' | 'resolved' | 'dismissed';
  reason: string | null;
  payload: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  dismissed_at: string | null;
}

export interface ActionItem {
  id: string;
  document_id: string;
  content: string;
  state: 'open' | 'completed' | 'dismissed';
  source: string;
  action_metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  dismissed_at: string | null;
}

export interface ReviewMetrics {
  open_review_count: number;
  resolved_review_count: number;
  dismissed_review_count: number;
  open_by_type: Record<string, number>;
  open_by_priority: Record<string, number>;
  average_age_hours: number;
  oldest_open_items: Array<Record<string, unknown>>;
  recently_resolved_count: number;
  low_confidence_category_count: number;
  uncategorized_count: number;
}

export interface ActionItemMetrics {
  open_count: number;
  completed_count: number;
  dismissed_count: number;
  overdue_count?: number | null;
  completion_rate: number;
  recently_completed_count: number;
}

export interface ReviewAuditEvent {
  id: string;
  document_id: string;
  actor_id: string | null;
  event_type: string;
  note: string | null;
  before_json: Record<string, unknown>;
  after_json: Record<string, unknown>;
  created_at: string;
  role: "viewer" | "editor" | "admin";
}

export interface RelationshipReviewItem {
  id: string;
  source_document_id: string;
  target_document_id: string;
  relationship_type: 'duplicate' | 'similar' | 'related' | 'thread' | 'attachment';
  confidence: number | null;
  source_document_title?: string | null;
  source_document_name?: string | null;
  source_document_snippet?: string | null;
  target_document_title?: string | null;
  target_document_name?: string | null;
  target_document_snippet?: string | null;
  source_snippet?: string | null;
  target_snippet?: string | null;
  status: 'pending' | 'confirmed' | 'dismissed';
  reason_codes_json: string[];
  metadata_json: Record<string, unknown>;
  created_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
}

export interface DocumentRelationshipListItem {
  id: string;
  status: 'pending' | 'confirmed' | 'dismissed';
  relationship_type: 'duplicate' | 'similar' | 'related' | 'thread' | 'attachment';
  confidence: number | null;
  related_document_id: string;
  related_document_title: string;
  related_document_name: string;
  related_document_snippet: string;
  direction: 'source' | 'target';
  created_at: string;
  updated_at: string | null;
  explanation_metadata?: {
    confidence?: number;
    signals?: string[];
    reason?: string;
  } | null;
}

export interface DocumentCluster {
  cluster_id: string;
  document_ids: string[];
  document_titles: string[];
  relationship_count: number;
  dominant_signals: string[];
}


export interface AdminUser { id: string; email: string; display_name: string; role: string; created_at: string; is_active: boolean; }
export interface AdminUsersPage { items: AdminUser[]; total_count: number; limit: number; offset: number; }
export interface AdminAuditEvent { id: string; actor_id: string | null; actor_email: string | null; entity_type: string; entity_id: string; action: string; details: Record<string, unknown>; created_at: string; }
export interface AdminAuditPage { items: AdminAuditEvent[]; total_count: number; limit: number; offset: number; }
export interface AdminMetrics { total_users: number; total_documents: number; documents_processed: number; documents_failed: number; pending_review_items: number; open_action_items: number; pending_relationship_reviews: number; }
export interface AdminProcessingSummary { pending: number; processing: number; completed: number; failed: number; recently_failed: number; }
export type PromptTemplateType = 'chat' | 'retrieval' | 'report' | 'timeline_extraction' | 'relationship_detection';
export interface PromptTemplate { id: string; prompt_type: PromptTemplateType; name: string; content: string; version: number; is_active: boolean; provider: "openai"|"gemini"; model: string; temperature: number; max_tokens: number; top_p: number; enabled: boolean; is_default: boolean; fallback_enabled: boolean; fallback_provider: "openai"|"gemini" | null; fallback_model: string | null; created_at: string; updated_at: string; }
export interface PromptTemplateCreateRequest { prompt_type: PromptTemplateType; name: string; content: string; provider: "openai"|"gemini"; model: string; temperature: number; max_tokens: number; top_p: number; enabled: boolean; is_default: boolean; fallback_enabled: boolean; fallback_provider?: "openai"|"gemini" | null; fallback_model?: string | null; }
export interface PromptTemplateUpdateRequest { name?: string; content?: string; provider?: "openai"|"gemini"; model?: string; temperature?: number; max_tokens?: number; top_p?: number; enabled?: boolean; is_default?: boolean; fallback_enabled?: boolean; fallback_provider?: "openai"|"gemini" | null; fallback_model?: string | null; }
export interface PromptTemplateTestRequest { prompt_type: PromptTemplateType; prompt_content: string; sample_context: string; provider: "openai"|"gemini"; model: string; temperature: number; max_tokens: number; top_p: number; fallback_enabled?: boolean; fallback_provider?: "openai"|"gemini" | null; fallback_model?: string | null; }
export interface PromptTemplateTestResponse { preview: string; latency_ms: number | null; usage_tokens: number | null; fallback_used: boolean; provider_used: string; model_used: string; primary_error: string | null; }
export interface LlmModelOption { id: string; name: string; }
export interface LlmProviderCatalog { id: 'openai' | 'gemini'; name: string; configured: boolean; models: LlmModelOption[]; }
export interface AdminLlmModelsResponse { providers: LlmProviderCatalog[]; }


export interface ChatbotSettings {
  system_prompt: string;
  retrieval_prompt: string;
  report_prompt: string;
  citation_prompt: string;
  default_report_template: string;
  model: string;
  temperature: number;
  max_tokens: number;
  max_documents: number;
  allow_full_text_retrieval: boolean;
}

export interface SourceRef {
  document_id?: string | null;
  document_title?: string | null;
  source_type?: string | null;
  kind?: string | null;
  preview?: string | null;
  title?: string | null;
  snippet?: string | null;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  source_refs?: SourceRef[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  title?: string | null;
  created_at: string;
  updated_at?: string | null;
  messages?: ChatMessage[];
}

export interface ChatMessageRequest {
  message: string;
  document_ids?: string[];
  include_timeline?: boolean;
  include_full_text?: boolean;
}

export interface ChatMessageResponse {
  session_id: string;
  answer: string;
  message: ChatMessage;
  source_refs: SourceRef[];
}

export interface ChatStreamChunkEvent {
  type: 'chunk';
  content: string;
}

export interface ChatStreamFinalEvent {
  type: 'final';
  content: string;
  source_refs: SourceRef[];
}

export type ChatStreamEvent = ChatStreamChunkEvent | ChatStreamFinalEvent;

export interface ReportCreateRequest {
  title: string;
  prompt: string;
  document_ids?: string[];
  include_timeline?: boolean;
  include_relationships?: boolean;
  include_full_text?: boolean;
}

export interface GeneratedReport {
  id: string;
  title: string;
  prompt: string;
  markdown_content?: string;
  sections?: {
    executive_summary?: string | null;
    summary?: string | null;
    timeline?: string | null;
    timeline_analysis?: string | null;
    relationships?: string | null;
    relationship_analysis?: string | null;
  } | null;
  insights?: StructuredInsight[];
  source_refs: SourceRef[];
  created_at: string;
}

export interface ReportUpdateRequest {
  title?: string;
  sections?: Record<string, string | null | undefined>;
}


export interface GmailPreviewRequest { sender_email: string; max_results: number; include_attachments: boolean; }
export interface GmailPreviewMessage { gmail_message_id: string; sender: string; subject: string; received_at: string | null; snippet: string; already_imported: boolean; attachments: string[]; }
export interface GmailPreviewResponse { messages: GmailPreviewMessage[]; }
export interface GmailImportResponse { imported_count: number; imported_email_count: number; imported_attachment_count: number; skipped_attachment_count: number; skipped_attachments: Array<{ filename: string; reason: string }>; duplicate_message_count: number; created_document_ids: string[]; }

export interface SubscriptionSummary {
  status: string;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  plan: {
    slug: string;
    name: string;
    price_monthly_cents: number;
    currency: string;
  };
}

export interface PlanSummary {
  slug: string;
  name: string;
  price_monthly_cents: number;
  currency: string;
  limits: Record<string, number | null>;
  features: Record<string, boolean>;
  is_current: boolean;
}

export interface UsageMetric { used: number; limit: number | null; }
export interface UsageSummary {
  plan: 'free' | 'pro' | string;
  documents: UsageMetric;
  reports: UsageMetric;
  chat_messages: UsageMetric;
}


export interface AdminSubscription {
  user_id: string;
  email: string;
  subscription_id: string;
  plan_slug: string;
  plan_name: string;
  status: string;
  cancel_at_period_end: boolean;
  usage_credits: Record<string, number>;
  limit_overrides: Record<string, number>;
}

export interface AdminUsageSummary {
  user_id: string;
  window_start: string;
  window_end: string;
  usage: Record<string, unknown>;
}

export interface AdminPlan {
  id: string;
  slug: 'free' | 'pro' | 'team' | string;
  name: string;
  price_monthly_cents: number;
  currency: string;
  limits_json: Record<string, number | null>;
  features_json: Record<string, boolean>;
  is_active: boolean;
}

export interface AdminSystemStatus {
  billing_configured: boolean;
  stripe_configured: boolean;
  stripe_prices_configured: boolean;
  environment: 'development' | 'staging' | 'production';
  limits_configured: boolean;
  features: {
    insights_enabled: boolean;
    category_intelligence_enabled: boolean;
    relationship_detection_enabled: boolean;
  };
}

export interface AdminPromptExecutionSummaryFilters {
  provider?: string;
  model?: string;
  source?: string;
  success?: boolean;
  fallback_used?: boolean;
  created_after?: string;
  created_before?: string;
}

export interface PromptExecutionLog { id: string; prompt_template_id: string | null; purpose: string | null; actor_user_id: string | null; provider: string; model: string; fallback_used: boolean; primary_error: string | null; latency_ms: number | null; input_tokens: number | null; output_tokens: number | null; total_tokens: number | null; success: boolean; error_message: string | null; source: string | null; estimated_cost_usd: number | null; currency: string | null; pricing_known: boolean; created_at: string; }

export interface PromptExecutionSummary {
  total_calls: number;
  success_rate: number;
  fallback_rate: number;
  avg_latency_ms: number | null;
  total_tokens: number;
  calls_by_provider: Record<string, number>;
  calls_by_model: Record<string, number>;
  total_estimated_cost_usd: number;
  cost_by_provider: Record<string, number>;
  cost_by_model: Record<string, number>;
  pricing_unknown_count: number;
  calls_by_source: Record<string, number>;
  failures_by_provider: Record<string, number>;
  fallback_by_provider: Record<string, number>;
}

export interface AdminInvite { id: string; email: string; role: string; status: string; created_at: string; dev_invite_link?: string | null; }
