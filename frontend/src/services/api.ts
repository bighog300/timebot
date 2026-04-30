import axios from 'axios';
import { http } from '@/services/http';
import type {
  ActionItem,
  ActionItemMetrics,
  Connection,
  ConnectStartResponse,
  Document,
  DocumentIntelligence,
  InsightsResponse,
  QueueItem,
  QueueStats,
  RelationshipReviewItem,
  ReviewAuditEvent,
  ReviewItem,
  ReviewMetrics,
  SearchResponse,
  SemanticSearchResponse,
  SyncLog,
  SyncRunResponse,
  TimelineResponse,
  AdminUsersPage,
  AdminMetrics,
  AdminAuditPage,
} from '@/types/api';

export const api = {

  listAdminUsers: async (limit = 20, offset = 0): Promise<AdminUsersPage> => (await http.get('/admin/users', { params: { limit, offset } })).data,
  updateAdminUserRole: async (userId: string, role: string) => (await http.patch(`/admin/users/${userId}/role`, { role })).data,
  getAdminMetrics: async (): Promise<AdminMetrics> => (await http.get('/admin/metrics')).data,
  listAdminAudit: async (limit = 20, offset = 0): Promise<AdminAuditPage> => (await http.get('/admin/audit', { params: { limit, offset } })).data,
  listDocuments: async (includeArchived = false): Promise<Document[]> =>
    (await http.get('/documents', { params: { include_archived: includeArchived } })).data,
  getDocument: async (id: string): Promise<Document> => (await http.get(`/documents/${id}`)).data,
  uploadDocument: async (file: File, token: string): Promise<Document> => {
    const body = new FormData();
    body.append('file', file);
    try {
      return (
        await http.post('/upload/', body, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
      ).data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error('Upload failed:', error.response?.data ?? error.message);
      } else {
        console.error('Upload failed:', error);
      }
      throw error;
    }
  },
  updateDocument: async (id: string, patch: Partial<Document>): Promise<Document> =>
    (await http.put(`/documents/${id}`, patch)).data,
  deleteDocument: async (id: string): Promise<void> => {
    await http.delete(`/documents/${id}`);
  },
  reprocessDocument: async (id: string): Promise<void> => {
    await http.post(`/documents/${id}/reprocess`);
  },
  searchKeyword: async (query: string): Promise<SearchResponse> =>
    (await http.post('/search/', null, { params: { query } })).data,
  searchSemantic: async (query: string): Promise<SemanticSearchResponse> =>
    (await http.post('/search/semantic', null, { params: { query } })).data,
  listSuggestions: async (q: string): Promise<string[]> =>
    (await http.get('/search/suggestions', { params: { q } })).data.suggestions,
  listFacets: async (query?: string): Promise<Record<string, unknown>> =>
    (await http.get('/search/facets', { params: { query } })).data,
  findSimilar: async (id: string): Promise<SemanticSearchResponse> =>
    (await http.get(`/search/documents/${id}/similar`)).data,
  getTimeline: async (): Promise<TimelineResponse> => (await http.get('/search/timeline')).data,
  listCategories: async (): Promise<Array<{ id: string; name: string; color: string; document_count: number }>> =>
    (await http.get('/categories')).data,
  getQueueStats: async (): Promise<QueueStats> => (await http.get('/queue/stats')).data,
  getQueueItems: async (): Promise<QueueItem[]> => (await http.get('/queue/items')).data,
  getReviewQueue: async (): Promise<Document[]> => (await http.get('/documents/review-queue')).data,
  listReviewItems: async (status: 'open' | 'resolved' | 'dismissed' = 'open', limit = 20, offset = 0): Promise<{items: ReviewItem[]; total_count:number; limit:number; offset:number}> =>
    (await http.get('/review/items', { params: { status, limit, offset } })).data,
  resolveReviewItem: async (id: string, note?: string): Promise<ReviewItem> =>
    (await http.post(`/review/items/${id}/resolve`, { note })).data,
  dismissReviewItem: async (id: string, note?: string): Promise<ReviewItem> =>
    (await http.post(`/review/items/${id}/dismiss`, { note })).data,
  bulkResolveReviewItems: async (ids: string[], note?: string): Promise<{ updated_count: number; skipped_count: number; items: ReviewItem[] }> =>
    (await http.post('/review/items/bulk-resolve', { ids, note })).data,
  bulkDismissReviewItems: async (ids: string[], note?: string): Promise<{ updated_count: number; skipped_count: number; items: ReviewItem[] }> =>
    (await http.post('/review/items/bulk-dismiss', { ids, note })).data,
  getReviewMetrics: async (): Promise<ReviewMetrics> => (await http.get('/review/metrics')).data,
  listReviewAuditEvents: async (documentId?: string): Promise<ReviewAuditEvent[]> =>
    (await http.get('/review/audit', { params: documentId ? { document_id: documentId } : undefined })).data,
  listRelationshipReviews: async (status: 'pending' | 'confirmed' | 'dismissed' = 'pending'): Promise<RelationshipReviewItem[]> =>
    (await http.get('/review/relationships', { params: { status } })).data,
  confirmRelationshipReview: async (id: string): Promise<RelationshipReviewItem> =>
    (await http.post(`/review/relationships/${id}/confirm`, { reason_codes_json: [], metadata_json: {} })).data,
  dismissRelationshipReview: async (id: string): Promise<RelationshipReviewItem> =>
    (await http.post(`/review/relationships/${id}/dismiss`, { reason_codes_json: [], metadata_json: {} })).data,
  getDocumentIntelligence: async (id: string): Promise<DocumentIntelligence> => (await http.get(`/documents/${id}/intelligence`)).data,
  patchDocumentIntelligence: async (
    id: string,
    patch: Partial<Pick<DocumentIntelligence, 'summary' | 'key_points' | 'suggested_tags' | 'entities' | 'model_metadata'>>,
  ): Promise<DocumentIntelligence> => (await http.patch(`/documents/${id}/intelligence`, patch)).data,
  approveDocumentCategory: async (id: string): Promise<Document> => (await http.post(`/documents/${id}/category/approve`)).data,
  overrideDocumentCategory: async (id: string, categoryId: string): Promise<Document> =>
    (await http.post(`/documents/${id}/category/override`, { category_id: categoryId })).data,
  getDocumentAuditHistory: async (id: string): Promise<ReviewAuditEvent[]> => (await http.get(`/documents/${id}/review-audit`)).data,
  listActionItems: async (status?: 'open' | 'completed' | 'dismissed', limit = 20, offset = 0): Promise<{items: ActionItem[]; total_count:number; limit:number; offset:number}> =>
    (await http.get('/action-items', { params: { status, limit, offset } })).data,
  completeActionItem: async (id: string): Promise<ActionItem> => (await http.post(`/action-items/${id}/complete`)).data,
  dismissActionItem: async (id: string): Promise<ActionItem> => (await http.post(`/action-items/${id}/dismiss`)).data,
  bulkCompleteActionItems: async (ids: string[], note?: string): Promise<{ updated_count: number; skipped_count: number; items: ActionItem[] }> =>
    (await http.post('/action-items/bulk-complete', { ids, note })).data,
  bulkDismissActionItems: async (ids: string[], note?: string): Promise<{ updated_count: number; skipped_count: number; items: ActionItem[] }> =>
    (await http.post('/action-items/bulk-dismiss', { ids, note })).data,
  listDocumentActionItems: async (documentId: string): Promise<ActionItem[]> => (await http.get(`/documents/${documentId}/action-items`)).data,
  getActionItemMetrics: async (): Promise<ActionItemMetrics> => (await http.get('/action-items/metrics')).data,
  reviewDocument: async (
    id: string,
    action: 'approve' | 'reject' | 'edit',
    overrideSummary?: string,
    overrideTags?: string[],
  ): Promise<Document> =>
    (
      await http.post(`/documents/${id}/review`, {
        action,
        override_summary: overrideSummary,
        override_tags: overrideTags,
      })
    ).data,
  retryFailedQueue: async (): Promise<{ message: string }> => (await http.post('/queue/retry-failed')).data,
  getInsightsOverview: async (): Promise<InsightsResponse> => (await http.get('/insights/overview')).data,
  getInsightsTrends: async (): Promise<{ lookback_days: number; trends: Array<Record<string, unknown>> }> =>
    (await http.get('/insights/trends')).data,
  getInsightsRollups: async (): Promise<Record<string, unknown>> => (await http.get('/insights/rollups')).data,
  listConnections: async (): Promise<Connection[]> => (await http.get('/connections')).data,
  startConnectProvider: async (type: string): Promise<ConnectStartResponse> =>
    (await http.post(`/connections/${type}/connect/start`)).data,
  completeConnectProvider: async (type: string, code: string, state: string): Promise<Connection> =>
    (await http.get(`/connections/${type}/connect/callback`, { params: { code, state } })).data,
  disconnectProvider: async (type: string): Promise<Connection> => (await http.post(`/connections/${type}/disconnect`)).data,
  syncProvider: async (type: string): Promise<SyncRunResponse> => (await http.post(`/connections/${type}/sync`)).data,
  getSyncLogs: async (type: string): Promise<SyncLog[]> => (await http.get(`/connections/${type}/sync-logs`)).data,
};
