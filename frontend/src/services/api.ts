import axios from 'axios';
import { http } from '@/services/http';
import type {
  ActionItem,
  ActionItemMetrics,
  Connection,
  ConnectStartResponse,
  Document,
  DocumentCluster,
  DocumentIntelligence,
  DocumentRelationshipListItem,
  InsightsResponse,
  StructuredInsight,
  StructuredInsightsResponse,
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
  AdminUser,
  AdminMetrics,
  AdminProcessingSummary,
  AdminAuditPage,
  ChatbotSettings,
  ChatSession,
  ChatMessageResponse,
  ChatMessageRequest,
  ChatStreamEvent,
  GeneratedReport,
  ReportCreateRequest,
  ReportUpdateRequest,
  GmailPreviewRequest,
  GmailPreviewResponse,
  GmailImportResponse,
  PromptTemplate,
  PromptTemplateCreateRequest,
  PromptTemplateUpdateRequest,
  PromptTemplateTestRequest,
  PromptTemplateTestResponse,
  PromptExecutionLog,
  PromptExecutionSummary,
  AdminPromptExecutionSummaryFilters,
  UsageSummary,
  SubscriptionSummary,
  PlanSummary,
  AdminSubscription,
  AdminUsageSummary,
  AdminSystemStatus,
  AdminLlmModelsResponse,
  AdminInvite,
} from '@/types/api';



export function getErrorDetail(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => (typeof item?.msg === 'string' ? item.msg : JSON.stringify(item))).join('; ');
    }
    if (detail && typeof detail === 'object') {
      const message = (detail as { message?: unknown }).message;
      if (typeof message === 'string') return message;
      return JSON.stringify(detail);
    }
    return error.message;
  }
  return error instanceof Error ? error.message : 'Unexpected error';
}

export const api = {

  getChatbotSettings: async (): Promise<ChatbotSettings> => (await http.get('/admin/chatbot-settings')).data,
  updateChatbotSettings: async (payload: ChatbotSettings): Promise<ChatbotSettings> => (await http.put('/admin/chatbot-settings', payload)).data,
  resetChatbotSettings: async (): Promise<ChatbotSettings> => (await http.post('/admin/chatbot-settings/reset')).data,
  createChatSession: async (title?: string): Promise<ChatSession> => (await http.post('/chat/sessions', { title })).data,
  listChatSessions: async (): Promise<ChatSession[]> => (await http.get('/chat/sessions')).data,
  getChatSession: async (sessionId: string): Promise<ChatSession> => (await http.get(`/chat/sessions/${sessionId}`)).data,
  sendChatMessage: async (sessionId: string, payload: ChatMessageRequest): Promise<ChatMessageResponse> => (await http.post(`/chat/sessions/${sessionId}/messages`, payload)).data,
  sendChatMessageStream: async (
    sessionId: string,
    payload: ChatMessageRequest,
    handlers: {
      onEvent: (event: ChatStreamEvent) => void;
      signal?: AbortSignal;
    },
  ): Promise<void> => {
    const response = await fetch(`${http.defaults.baseURL}/chat/sessions/${sessionId}/messages/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...(http.defaults.headers.common.Authorization ? { Authorization: String(http.defaults.headers.common.Authorization) } : {}),
      },
      body: JSON.stringify(payload),
      signal: handlers.signal,
    });
    if (!response.ok || !response.body) {
      throw new Error(`Streaming failed (${response.status})`);
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split('\n\n');
      buffer = frames.pop() ?? '';
      for (const frame of frames) {
        const lines = frame.split('\n').map((line) => line.trim());
        const eventName = lines.find((line) => line.startsWith('event:'))?.replace(/^event:\s?/, '');
        const dataLines = lines.filter((line) => line.startsWith('data:')).map((line) => line.replace(/^data:\s?/, ''));
        if (dataLines.length === 0) continue;
        const raw = dataLines.join('\n');
        try {
          const payload = JSON.parse(raw) as Partial<ChatStreamEvent> & {
            delta?: string;
            message?: string;
            source_refs?: ChatStreamEvent extends { source_refs: infer T } ? T : never;
          };

          if (eventName === 'chunk' && typeof payload.delta === 'string') {
            handlers.onEvent({ type: 'chunk', content: payload.delta });
            continue;
          }

          if (eventName === 'final' && typeof payload.message === 'string') {
            handlers.onEvent({ type: 'final', content: payload.message, source_refs: Array.isArray(payload.source_refs) ? payload.source_refs : [] });
            continue;
          }

          if (payload.type === 'chunk' && typeof payload.content === 'string') {
            handlers.onEvent({ type: 'chunk', content: payload.content });
            continue;
          }

          if (payload.type === 'final' && typeof payload.content === 'string') {
            handlers.onEvent({ type: 'final', content: payload.content, source_refs: Array.isArray(payload.source_refs) ? payload.source_refs : [] });
          }
        } catch {
          // Ignore malformed stream event payloads and keep stream alive.
        }
      }
    }
  },
  createReport: async (payload: ReportCreateRequest): Promise<GeneratedReport> => (await http.post('/reports', payload)).data,
  getUsage: async (): Promise<UsageSummary> => (await http.get('/me/usage')).data,
  getSubscription: async (): Promise<SubscriptionSummary> => (await http.get('/me/subscription')).data,
  listPlans: async (): Promise<PlanSummary[]> => (await http.get('/plans')).data,
  createCheckoutSession: async (plan: string): Promise<{ checkout_session_id: string; checkout_url: string; plan: string }> => (await http.post('/billing/checkout-session', { plan })).data,
  createCustomerPortalSession: async (): Promise<{ portal_url: string }> => (await http.post('/billing/customer-portal')).data,
  listReports: async (): Promise<GeneratedReport[]> => (await http.get('/reports')).data,
  getReport: async (reportId: string): Promise<GeneratedReport> => (await http.get(`/reports/${reportId}`)).data,
  updateReport: async (reportId: string, payload: ReportUpdateRequest): Promise<GeneratedReport> => (await http.patch(`/reports/${reportId}`, payload)).data,
  getReportDownloadUrl: (reportId: string, format: 'md' | 'pdf' = 'md'): string =>
    `${http.defaults.baseURL}/reports/${reportId}/download?format=${format}`,

  listAdminUsers: async (limit = 20, offset = 0, filters: { q?: string; role?: string; status?: string } = {}): Promise<AdminUsersPage> => (await http.get('/admin/users', { params: { limit, offset, ...filters } })).data,
  updateAdminUserRole: async (userId: string, role: string) => (await http.patch(`/admin/users/${userId}/role`, { role })).data,

  createAdminUser: async (payload: { email: string; display_name: string; role: string }): Promise<AdminUser> => (await http.post('/admin/users', payload)).data,
  deactivateAdminUser: async (userId: string): Promise<void> => { await http.post(`/admin/users/${userId}/deactivate`); },
  reactivateAdminUser: async (userId: string): Promise<void> => { await http.post(`/admin/users/${userId}/reactivate`); },
  deleteAdminUser: async (userId: string): Promise<void> => { await http.delete(`/admin/users/${userId}`); },
  listAdminInvites: async (): Promise<AdminInvite[]> => (await http.get('/admin/users/invites')).data,
  inviteAdminUser: async (payload: { email: string; display_name: string; role: string }): Promise<AdminInvite> => (await http.post('/admin/users/invite', payload)).data,
  resendAdminInvite: async (inviteId: string): Promise<void> => { await http.post(`/admin/users/invites/${inviteId}/resend`); },
  cancelAdminInvite: async (inviteId: string): Promise<void> => { await http.post(`/admin/users/invites/${inviteId}/cancel`); },

  getAdminMetrics: async (): Promise<AdminMetrics> => (await http.get('/admin/metrics')).data,
  getAdminProcessingSummary: async (): Promise<AdminProcessingSummary> => (await http.get('/admin/processing-summary')).data,
  listAdminAudit: async (limit = 20, offset = 0): Promise<AdminAuditPage> => (await http.get('/admin/audit', { params: { limit, offset } })).data,

  listAdminSubscriptions: async (): Promise<AdminSubscription[]> => (await http.get('/admin/subscriptions')).data,
  getAdminUsageSummary: async (userId: string): Promise<AdminUsageSummary> => (await http.get(`/admin/users/${userId}/usage-summary`)).data,
  getAdminSystemStatus: async (): Promise<AdminSystemStatus> => (await http.get('/admin/system-status')).data,
  getAdminLlmModels: async (): Promise<AdminLlmModelsResponse> => (await http.get('/admin/llm-models')).data,
  updateAdminUserPlan: async (userId: string, planSlug: string): Promise<AdminSubscription> => (await http.patch(`/admin/users/${userId}/plan`, { plan_slug: planSlug })).data,
  updateAdminUsageControls: async (userId: string, usageCredits: Record<string, number>, limitOverrides: Record<string, number | null>): Promise<AdminSubscription> => (await http.patch(`/admin/users/${userId}/usage-controls`, { usage_credits: usageCredits, limit_overrides: limitOverrides })).data,
  cancelOrDowngradeAdminSubscription: async (userId: string, downgradeToPlanSlug: string): Promise<AdminSubscription> => (await http.post(`/admin/users/${userId}/cancel-or-downgrade`, { downgrade_to_plan_slug: downgradeToPlanSlug })).data,

  listPromptTemplates: async (): Promise<PromptTemplate[]> => (await http.get('/admin/prompts')).data,
  createPromptTemplate: async (payload: PromptTemplateCreateRequest): Promise<PromptTemplate> => (await http.post('/admin/prompts', payload)).data,
  updatePromptTemplate: async (promptId: string, payload: PromptTemplateUpdateRequest): Promise<PromptTemplate> => (await http.put(`/admin/prompts/${promptId}`, payload)).data,
  activatePromptTemplate: async (promptId: string): Promise<PromptTemplate> => (await http.post(`/admin/prompts/${promptId}/activate`)).data,
  testPromptTemplate: async (payload: PromptTemplateTestRequest): Promise<PromptTemplateTestResponse> => (await http.post(`/admin/prompts/test`, { type: payload.prompt_type, content: payload.prompt_content, sample_context: payload.sample_context, provider: payload.provider, model: payload.model, temperature: payload.temperature, max_tokens: payload.max_tokens, top_p: payload.top_p, fallback_enabled: payload.fallback_enabled, fallback_provider: payload.fallback_provider, fallback_model: payload.fallback_model })).data,
  listPromptExecutions: async (): Promise<PromptExecutionLog[]> => (await http.get('/admin/prompt-executions')).data,
  getPromptExecutionSummary: async (filters: AdminPromptExecutionSummaryFilters = {}): Promise<PromptExecutionSummary> => (await http.get('/admin/prompt-executions/summary', { params: filters })).data,
  listDocuments: async (includeArchived = false): Promise<Document[]> =>
    (await http.get('/documents/', { params: { include_archived: includeArchived } })).data,
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
  getDocumentIntelligence: async (id: string): Promise<DocumentIntelligence | null> => (await http.get(`/documents/${id}/intelligence`)).data,
  patchDocumentIntelligence: async (
    id: string,
    patch: Partial<Pick<DocumentIntelligence, 'summary' | 'key_points' | 'suggested_tags' | 'entities' | 'model_metadata'>>,
  ): Promise<DocumentIntelligence> => (await http.patch(`/documents/${id}/intelligence`, patch)).data,
  approveDocumentCategory: async (id: string): Promise<Document> => (await http.post(`/documents/${id}/category/approve`)).data,
  overrideDocumentCategory: async (id: string, categoryId: string): Promise<Document> =>
    (await http.post(`/documents/${id}/category/override`, { category_id: categoryId })).data,
  getDocumentAuditHistory: async (id: string): Promise<ReviewAuditEvent[]> => (await http.get(`/documents/${id}/review-audit`)).data,
  listDocumentRelationships: async (id: string, params?: { include_dismissed?: boolean; status?: 'pending' | 'confirmed' | 'dismissed'; limit?: number }): Promise<DocumentRelationshipListItem[]> =>
    (await http.get(`/documents/${id}/relationships`, { params })).data,
  listDocumentClusters: async (): Promise<DocumentCluster[]> =>
    (await http.get('/documents/clusters')).data,
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
  getStructuredInsights: async (): Promise<StructuredInsight[]> => {
    const data = (await http.get('/insights/structured')).data as StructuredInsight[] | StructuredInsightsResponse | null | undefined;
    if (Array.isArray(data)) return data;
    return Array.isArray(data?.insights) ? data.insights : [];
  },
  listConnections: async (): Promise<Connection[]> => (await http.get('/connections')).data,
  startConnectProvider: async (type: string): Promise<ConnectStartResponse> =>
    (await http.post(`/connections/${type}/connect/start`)).data,
  completeConnectProvider: async (type: string, code: string, state: string): Promise<Connection> =>
    (await http.get(`/connections/${type}/connect/callback`, { params: { code, state } })).data,
  disconnectProvider: async (type: string): Promise<Connection> => (await http.post(`/connections/${type}/disconnect`)).data,
  syncProvider: async (type: string): Promise<SyncRunResponse> => (await http.post(`/connections/${type}/sync`)).data,
  getSyncLogs: async (type: string): Promise<SyncLog[]> => (await http.get(`/connections/${type}/sync-logs`)).data,
  gmailPreview: async (payload: GmailPreviewRequest): Promise<GmailPreviewResponse> => (await http.post('/imports/gmail/preview', payload)).data,
  gmailImport: async (payload: { sender_email: string; message_ids: string[]; include_attachments: boolean }): Promise<GmailImportResponse> => (await http.post('/imports/gmail/import', payload)).data,
};
