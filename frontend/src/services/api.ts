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
  AdminSystemHealth,
  AdminSystemJobs,
  AdminLlmMetrics,
  AdminInvite,
  AdminPlan,
  Workspace,
  WorkspaceMember,
  NotificationItem,
  MessageThread,
  EmailProviderConfig,
  EmailProviderConfigPatch,
  EmailTemplate,
  EmailTemplateCreate,
  EmailTemplatePatch,
  EmailTestSendRequest,
  EmailTestSendResult,
  EmailSendLog,
  EmailCampaign,
  EmailCampaignCreate,
  EmailCampaignPatch,
  EmailCampaignPreviewResponse,
  EmailCampaignTestSendRequest,
  CampaignRecipientPreview,
  CampaignSendRequest,
  CampaignSendResult,
  CampaignSendStatus,
  EmailSuppression,
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

const ALLOWED_PLAN_LIMIT_KEYS = ['documents_per_month', 'storage_bytes', 'processing_jobs_per_month', 'seats'] as const;
const ALLOWED_PLAN_FEATURE_KEYS = ['basic_search', 'chat', 'priority_support', 'team_workspace', 'insights_enabled', 'category_intelligence_enabled', 'relationship_detection_enabled'] as const;

type AdminPlanPatchPayload = Partial<Pick<AdminPlan, 'name' | 'price_monthly_cents' | 'limits_json' | 'features_json' | 'is_active'>>;

export function normalizeAdminPlanPatchPayload(payload: AdminPlanPatchPayload): AdminPlanPatchPayload {
  const normalized: AdminPlanPatchPayload = {};

  if (typeof payload.name === 'string') normalized.name = payload.name;
  if (typeof payload.is_active === 'boolean') normalized.is_active = payload.is_active;

  if (payload.price_monthly_cents !== undefined && payload.price_monthly_cents !== null) {
    const parsed = Number(payload.price_monthly_cents as unknown);
    if (Number.isFinite(parsed)) normalized.price_monthly_cents = parsed;
  }

  if (payload.limits_json && typeof payload.limits_json === 'object') {
    const limits: Record<string, number | null> = {};
    for (const key of ALLOWED_PLAN_LIMIT_KEYS) {
      const value: unknown = payload.limits_json[key];
      if (value === undefined) continue;
      if (value === null || (typeof value === 'string' && value.trim() === '')) {
        limits[key] = null;
        continue;
      }
      const parsed = Number(value);
      if (Number.isFinite(parsed)) limits[key] = parsed;
    }
    normalized.limits_json = limits;
  }

  if (payload.features_json && typeof payload.features_json === 'object') {
    const features: Record<string, boolean> = {};
    for (const key of ALLOWED_PLAN_FEATURE_KEYS) {
      const value = payload.features_json[key];
      if (typeof value === 'boolean') features[key] = value;
    }
    normalized.features_json = features;
  }

  return normalized;
}

export const api = {
  listWorkspaces: async (): Promise<Workspace[]> => (await http.get("/workspaces")).data,
  getWorkspace: async (workspaceId: string): Promise<Workspace> => (await http.get(`/workspaces/${workspaceId}`)).data,
  createWorkspace: async (payload: { name: string }): Promise<Workspace> => (await http.post('/workspaces', payload)).data,
  inviteWorkspaceMember: async (workspaceId: string, payload: { email: string; role: string }): Promise<{ invite: { id: string; email: string; role: string }; token?: string | null }> => (await http.post(`/workspaces/${workspaceId}/invites`, payload)).data,
  acceptWorkspaceInvite: async (token: string): Promise<{ accepted: boolean }> => (await http.post(`/workspaces/invites/${token}/accept`)).data,
  updateWorkspaceMemberRole: async (workspaceId: string, userId: string, role: WorkspaceMember['role']): Promise<WorkspaceMember> => (await http.patch(`/workspaces/${workspaceId}/members/${userId}`, { role })).data,
  removeWorkspaceMember: async (workspaceId: string, userId: string): Promise<{ removed: boolean }> => (await http.delete(`/workspaces/${workspaceId}/members/${userId}`)).data,
  listNotifications: async (): Promise<NotificationItem[]> => (await http.get('/notifications')).data,
  markNotificationRead: async (id: string): Promise<void> => { await http.post(`/notifications/${id}/read`); },
  markAllNotificationsRead: async (): Promise<void> => { await http.post('/notifications/read-all'); },
  listMessages: async (): Promise<MessageThread[]> => (await http.get('/messages')).data,
  createMessageThread: async (payload: { category: string; subject: string; body: string; workspace_id?: string }): Promise<MessageThread> => (await http.post('/messages', payload)).data,
  getMessageThread: async (threadId: string): Promise<MessageThread> => (await http.get(`/messages/${threadId}`)).data,
  replyMessageThread: async (threadId: string, body: string): Promise<MessageThread> => (await http.post(`/messages/${threadId}/reply`, { body })).data,
  adminListMessages: async (params: { status?: string; category?: string } = {}): Promise<MessageThread[]> => (await http.get('/admin/messages', { params })).data,
  adminGetMessageThread: async (threadId: string): Promise<MessageThread> => (await http.get(`/admin/messages/${threadId}`)).data,
  adminReplyMessageThread: async (threadId: string, body: string): Promise<MessageThread> => (await http.post(`/admin/messages/${threadId}/reply`, { body })).data,
  adminPatchMessageThread: async (threadId: string, status: string): Promise<MessageThread> => (await http.patch(`/admin/messages/${threadId}`, { status })).data,

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
  listAdminPlans: async (): Promise<AdminPlan[]> => (await http.get('/admin/plans')).data,
  updateAdminPlan: async (planId: string, payload: AdminPlanPatchPayload): Promise<AdminPlan> => (await http.patch(`/admin/plans/${planId}`, normalizeAdminPlanPatchPayload(payload))).data,
  resetAdminPlanDefaults: async (): Promise<AdminPlan[]> => (await http.post('/admin/plans/reset-defaults')).data,
  getAdminUsageSummary: async (userId: string): Promise<AdminUsageSummary> => (await http.get(`/admin/users/${userId}/usage-summary`)).data,
  getAdminSystemStatus: async (): Promise<AdminSystemStatus> => (await http.get('/admin/system-status')).data,
  getAdminSystemHealth: async (): Promise<AdminSystemHealth> => (await http.get('/admin/system/health')).data,
  getAdminSystemJobs: async (): Promise<AdminSystemJobs> => (await http.get('/admin/system/jobs')).data,
  getAdminLlmMetrics: async (): Promise<AdminLlmMetrics> => (await http.get('/admin/system/llm-metrics')).data,
  getAdminLlmModels: async (): Promise<AdminLlmModelsResponse> => (await http.get('/admin/llm-models')).data,
  updateAdminUserPlan: async (userId: string, planSlug: string): Promise<AdminSubscription> => (await http.patch(`/admin/users/${userId}/plan`, { plan_slug: planSlug })).data,
  updateAdminUsageControls: async (userId: string, usageCredits: Record<string, number>, limitOverrides: Record<string, number | null>): Promise<AdminSubscription> => (await http.patch(`/admin/users/${userId}/usage-controls`, { usage_credits: usageCredits, limit_overrides: limitOverrides })).data,
  cancelOrDowngradeAdminSubscription: async (userId: string, downgradeToPlanSlug: string): Promise<AdminSubscription> => (await http.post(`/admin/users/${userId}/cancel-or-downgrade`, { downgrade_to_plan_slug: downgradeToPlanSlug })).data,


  listEmailProviderConfigs: async (): Promise<EmailProviderConfig[]> => (await http.get('/admin/email/providers')).data,
  getEmailProviderConfig: async (provider: 'resend'|'sendgrid'): Promise<EmailProviderConfig> => (await http.get(`/admin/email/providers/${provider}`)).data,
  patchEmailProviderConfig: async (provider: 'resend'|'sendgrid', payload: EmailProviderConfigPatch): Promise<EmailProviderConfig> => (await http.patch(`/admin/email/providers/${provider}`, payload)).data,
  listEmailTemplates: async (): Promise<EmailTemplate[]> => (await http.get('/admin/email/templates')).data,
  createEmailTemplate: async (payload: EmailTemplateCreate): Promise<EmailTemplate> => (await http.post('/admin/email/templates', payload)).data,
  getEmailTemplate: async (templateId: string): Promise<EmailTemplate> => (await http.get(`/admin/email/templates/${templateId}`)).data,
  patchEmailTemplate: async (templateId: string, payload: EmailTemplatePatch): Promise<EmailTemplate> => (await http.patch(`/admin/email/templates/${templateId}`, payload)).data,
  archiveEmailTemplate: async (templateId: string): Promise<EmailTemplate> => (await http.delete(`/admin/email/templates/${templateId}`)).data,
  listEmailCampaigns: async (): Promise<EmailCampaign[]> => (await http.get('/admin/email/campaigns')).data,
  createEmailCampaign: async (payload: EmailCampaignCreate): Promise<EmailCampaign> => (await http.post('/admin/email/campaigns', payload)).data,
  getEmailCampaign: async (campaignId: string): Promise<EmailCampaign> => (await http.get(`/admin/email/campaigns/${campaignId}`)).data,
  patchEmailCampaign: async (campaignId: string, payload: EmailCampaignPatch): Promise<EmailCampaign> => (await http.patch(`/admin/email/campaigns/${campaignId}`, payload)).data,
  archiveEmailCampaign: async (campaignId: string): Promise<EmailCampaign> => (await http.delete(`/admin/email/campaigns/${campaignId}`)).data,
  previewEmailCampaign: async (campaignId: string, payload: { variables_json?: Record<string, unknown> | null }): Promise<EmailCampaignPreviewResponse> => (await http.post(`/admin/email/campaigns/${campaignId}/preview`, payload)).data,
  previewCampaignRecipients: async (campaignId: string): Promise<CampaignRecipientPreview> => (await http.post(`/admin/email/campaigns/${campaignId}/recipients/preview`, {})).data,
  sendCampaign: async (campaignId: string, payload: CampaignSendRequest): Promise<CampaignSendResult> => (await http.post(`/admin/email/campaigns/${campaignId}/send`, payload)).data,
  getCampaignSendStatus: async (campaignId: string): Promise<CampaignSendStatus> => (await http.get(`/admin/email/campaigns/${campaignId}/send-status`)).data,
  testSendCampaign: async (campaignId: string, payload: EmailCampaignTestSendRequest): Promise<EmailTestSendResult> => (await http.post(`/admin/email/campaigns/${campaignId}/test-send`, payload)).data,
  testSendEmail: async (payload: EmailTestSendRequest): Promise<EmailTestSendResult> => (await http.post('/admin/email/test-send', payload)).data,
  getEmailSendLogs: async (): Promise<EmailSendLog[]> => (await http.get('/admin/email/send-logs')).data,
  listEmailSuppressions: async (): Promise<EmailSuppression[]> => (await http.get('/admin/email/suppressions')).data,
  addEmailSuppression: async (payload: {email: string; reason: 'unsubscribe'|'bounce'|'complaint'|'manual'; source?: string}): Promise<EmailSuppression> => (await http.post('/admin/email/suppressions', payload)).data,
  removeEmailSuppression: async (email: string): Promise<void> => { await http.delete(`/admin/email/suppressions/${encodeURIComponent(email)}`); },
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
