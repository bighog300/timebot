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
  status: 'connected' | 'disconnected' | 'error' | 'syncing';
  display_name: string;
  email?: string | null;
  last_sync_date?: string | null;
  last_sync_status?: 'success' | 'failed' | 'partial' | 'in_progress' | null;
  sync_progress: number;
  document_count: number;
  total_size: number;
  auto_sync: boolean;
  sync_interval: number;
  is_authenticated: boolean;
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
