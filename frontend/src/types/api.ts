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
  processing_error?: string | null;
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

export interface TimelineResponse {
  group_by: string;
  total_documents: number;
  total_events: number;
  buckets: Array<{ period: string; count: number; events: Array<Record<string, unknown>> }>;
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
}

export interface RelationshipReviewItem {
  id: string;
  source_document_id: string;
  target_document_id: string;
  relationship_type: 'duplicate' | 'similar' | 'related';
  confidence: number | null;
  status: 'pending' | 'confirmed' | 'dismissed';
  reason_codes_json: string[];
  metadata_json: Record<string, unknown>;
  created_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
}
