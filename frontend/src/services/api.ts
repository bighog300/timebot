import { http } from '@/services/http';
import type {
  Connection,
  ConnectStartResponse,
  Document,
  InsightsResponse,
  QueueItem,
  QueueStats,
  SearchResponse,
  SemanticSearchResponse,
  SyncLog,
  SyncRunResponse,
  TimelineResponse,
} from '@/types/api';

export const api = {
  listDocuments: async (includeArchived = false): Promise<Document[]> =>
    (await http.get('/documents', { params: { include_archived: includeArchived } })).data,
  getDocument: async (id: string): Promise<Document> => (await http.get(`/documents/${id}`)).data,
  uploadDocument: async (file: File): Promise<Document> => {
    const body = new FormData();
    body.append('file', file);
    return (await http.post('/upload', body)).data;
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
    (await http.post('/search', null, { params: { query } })).data,
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
