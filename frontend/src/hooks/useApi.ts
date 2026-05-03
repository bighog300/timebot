import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '@/auth/AuthContext';
import { api } from '@/services/api';
import type { ActionItem, PromptTemplateCreateRequest, PromptTemplateTestRequest, PromptTemplateUpdateRequest, RelationshipReviewItem, ReviewItem } from '@/types/api';
import type { DocumentRelationshipListItem } from '@/types/api';

type PaginatedData<T> = { items: T[]; total_count: number; limit: number; offset: number };

function updatePaginatedQueries<T>(
  qc: ReturnType<typeof useQueryClient>,
  baseKey: readonly unknown[],
  updater: (item: T) => T | null,
) {
  const entries = qc.getQueriesData<PaginatedData<T>>({ queryKey: baseKey });
  const previous = entries.map(([queryKey, data]) => [queryKey, data] as const);

  entries.forEach(([queryKey, data]) => {
    if (!data) return;
    const nextItems = data.items.map(updater).filter((item): item is T => item !== null);
    const nextTotal = Math.max(0, data.total_count - (data.items.length - nextItems.length));
    qc.setQueryData(queryKey, { ...data, items: nextItems, total_count: nextTotal });
  });

  return previous;
}

export const keys = {
  documents: ['documents'] as const,
  queueStats: ['queue-stats'] as const,
  queueItems: ['queue-items'] as const,
  reviewQueue: ['review-queue'] as const,
  reviewItems: (status: string) => ['review-items', status] as const,
  reviewMetrics: ['review-metrics'] as const,
  relationshipReviews: (status: string) => ['relationship-reviews', status] as const,
  actionItems: (state: string) => ['action-items', state] as const,
  actionItemMetrics: ['action-item-metrics'] as const,
  documentIntelligence: (documentId: string) => ['document-intelligence', documentId] as const,
  documentActionItems: (documentId: string) => ['document-action-items', documentId] as const,
  documentAuditHistory: (documentId: string) => ['document-audit-history', documentId] as const,
  documentRelationships: (documentId: string) => ['document-relationships', documentId] as const,
  documentClusters: ['document-clusters'] as const,
  categories: ['categories'] as const,
  search: ['search'] as const,
  timeline: ['timeline'] as const,
  insightsOverview: ['insights-overview'] as const,
  insightsStructured: ['insights-structured'] as const,
  suggestions: ['suggestions'] as const,
  facets: ['facets'] as const,
  connections: ['connections'] as const,
  adminUsers: (page:number,limit:number)=>['admin-users',page,limit] as const,
  adminMetrics: ['admin-metrics'] as const,
  adminProcessingSummary: ['admin-processing-summary'] as const,
  adminAudit: (page:number,limit:number)=>['admin-audit',page,limit] as const,
  adminSubscriptions: ['admin-subscriptions'] as const,
  adminUsageSummary: (userId: string) => ['admin-usage-summary', userId] as const,
  adminSystemStatus: ['admin-system-status'] as const,
  adminPrompts: ['admin-prompts'] as const,
  adminPromptExecutions: ['admin-prompt-executions'] as const,
  adminLlmModels: ['admin-llm-models'] as const,
  chatbotSettings: ['chatbot-settings'] as const,
  chatSessions: ['chat-sessions'] as const,
  chatSession: (sessionId: string) => ['chat-session', sessionId] as const,
  reports: ['reports'] as const,
  usage: ['usage'] as const,
  subscription: ['subscription'] as const,
  plans: ['plans'] as const,
  report: (reportId: string) => ['report', reportId] as const,
  gmailConnections: ['connections'] as const,
};

function useAuthReady() {
  const { token, loading } = useAuth();
  return Boolean(token) && !loading;
}

export function useDocuments() {
  const authReady = useAuthReady();
  return useQuery({
    queryKey: keys.documents,
    queryFn: () => api.listDocuments(false),
    enabled: authReady,
    refetchInterval: (query) => {
      const docs = query.state.data as Array<{ processing_status?: string }> | undefined;
      const hasInFlight = (docs ?? []).some((doc) => doc.processing_status === 'uploading' || doc.processing_status === 'processing');
      return hasInFlight ? 3000 : false;
    },
  });
}

export function useDocumentClusters() {
  const authReady = useAuthReady();
  return useQuery({
    queryKey: keys.documentClusters,
    queryFn: api.listDocumentClusters,
    enabled: authReady,
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  const { token, loading } = useAuth();
  return useMutation({
    mutationFn: async (file: File) => {
      if (loading) {
        throw new Error('Authentication is still loading. Please try again in a moment.');
      }
      if (!token) {
        throw new Error('You must be logged in to upload documents.');
      }
      return api.uploadDocument(file, token);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.documents });
      qc.invalidateQueries({ queryKey: keys.search });
      qc.invalidateQueries({ queryKey: keys.suggestions });
      qc.invalidateQueries({ queryKey: keys.facets });
      qc.invalidateQueries({ queryKey: keys.timeline });
      qc.invalidateQueries({ queryKey: keys.insightsOverview });
      qc.invalidateQueries({ queryKey: keys.insightsStructured });
      qc.invalidateQueries({ queryKey: keys.categories });
      qc.invalidateQueries({ queryKey: ['relationship-reviews'] });
    },
  });
}

export function useQueueStats() {
  const authReady = useAuthReady();
  return useQuery({ queryKey: keys.queueStats, queryFn: api.getQueueStats, refetchInterval: 5000, enabled: authReady });
}

export function useQueueItems() {
  const authReady = useAuthReady();
  return useQuery({ queryKey: keys.queueItems, queryFn: api.getQueueItems, refetchInterval: 5000, enabled: authReady });
}

export function useReviewQueue() {
  const authReady = useAuthReady();
  return useQuery({ queryKey: keys.reviewQueue, queryFn: api.getReviewQueue, refetchInterval: 5000, enabled: authReady });
}

export function useReviewDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, action, overrideSummary, overrideTags }: { id: string; action: 'approve' | 'reject' | 'edit'; overrideSummary?: string; overrideTags?: string[] }) =>
      api.reviewDocument(id, action, overrideSummary, overrideTags),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.reviewQueue });
      qc.invalidateQueries({ queryKey: keys.queueStats });
      qc.invalidateQueries({ queryKey: keys.documents });
      qc.invalidateQueries({ queryKey: keys.search });
      qc.invalidateQueries({ queryKey: keys.suggestions });
      qc.invalidateQueries({ queryKey: keys.facets });
      qc.invalidateQueries({ queryKey: keys.timeline });
      qc.invalidateQueries({ queryKey: keys.insightsOverview });
      qc.invalidateQueries({ queryKey: keys.insightsStructured });
      qc.invalidateQueries({ queryKey: keys.categories });
      qc.invalidateQueries({ queryKey: ['relationship-reviews'] });
    },
  });
}

export function useCategories() {
  const authReady = useAuthReady();
  return useQuery({ queryKey: keys.categories, queryFn: api.listCategories, enabled: authReady });
}

export function useReviewItems(status: 'open' | 'resolved' | 'dismissed', page = 0, limit = 20) {
  const authReady = useAuthReady();
  return useQuery({ queryKey: [...keys.reviewItems(status), page, limit], queryFn: () => api.listReviewItems(status, limit, page * limit), enabled: authReady });
}

export function useResolveReviewItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note?: string }) => api.resolveReviewItem(id, note),
    onMutate: async ({ id }) => {
      await qc.cancelQueries({ queryKey: ['review-items'] });
      const previous = updatePaginatedQueries<ReviewItem>(qc, keys.reviewItems('open'), (item) => (item.id === id ? null : item));
      return { previous };
    },
    onError: (_err, _vars, context) => {
      context?.previous?.forEach(([queryKey, data]) => qc.setQueryData(queryKey, data));
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['review-items'] });
      qc.invalidateQueries({ queryKey: keys.reviewMetrics });
    },
  });
}

export function useDismissReviewItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note?: string }) => api.dismissReviewItem(id, note),
    onMutate: async ({ id }) => {
      await qc.cancelQueries({ queryKey: ['review-items'] });
      const previous = updatePaginatedQueries<ReviewItem>(qc, keys.reviewItems('open'), (item) => (item.id === id ? null : item));
      return { previous };
    },
    onError: (_err, _vars, context) => {
      context?.previous?.forEach(([queryKey, data]) => qc.setQueryData(queryKey, data));
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['review-items'] });
      qc.invalidateQueries({ queryKey: keys.reviewMetrics });
    },
  });
}

export function useBulkResolveReviewItems() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ids, note }: { ids: string[]; note?: string }) => api.bulkResolveReviewItems(ids, note),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['review-items'] });
      qc.invalidateQueries({ queryKey: keys.reviewMetrics });
    },
  });
}

export function useBulkDismissReviewItems() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ids, note }: { ids: string[]; note?: string }) => api.bulkDismissReviewItems(ids, note),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['review-items'] });
      qc.invalidateQueries({ queryKey: keys.reviewMetrics });
    },
  });
}

export function useAdminPromptExecutionSummary(filters: { provider?: string; model?: string; source?: string; success?: boolean; fallback_used?: boolean; created_after?: string; created_before?: string } = {}) {
  const authReady = useAuthReady();
  return useQuery({ queryKey: [...keys.adminPromptExecutions, "summary", filters], queryFn: () => api.getPromptExecutionSummary(filters), enabled: authReady });
}

export function useReviewMetrics() {
  const authReady = useAuthReady();
  return useQuery({ queryKey: keys.reviewMetrics, queryFn: api.getReviewMetrics, enabled: authReady });
}

export function useRelationshipReviews(status: 'pending' | 'confirmed' | 'dismissed') {
  const authReady = useAuthReady();
  return useQuery({ queryKey: keys.relationshipReviews(status), queryFn: () => api.listRelationshipReviews(status), enabled: authReady });
}

export function useDocumentRelationships(documentId: string) {
  const authReady = useAuthReady();
  return useQuery<DocumentRelationshipListItem[]>({
    queryKey: keys.documentRelationships(documentId),
    queryFn: async () => {
      try {
        return await api.listDocumentRelationships(documentId);
      } catch (error) {
        if (axios.isAxiosError(error)) {
          const detail = typeof error.response?.data?.detail === 'string' ? error.response.data.detail : null;
          throw new Error(detail ?? error.message);
        }
        throw error;
      }
    },
    enabled: authReady && Boolean(documentId),
  });
}

export function useConfirmRelationshipReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.confirmRelationshipReview(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: keys.relationshipReviews('pending') });
      const previous = qc.getQueriesData<RelationshipReviewItem[]>({ queryKey: keys.relationshipReviews('pending') });
      previous.forEach(([queryKey, data]) => {
        if (!data) return;
        qc.setQueryData(queryKey, data.filter((item) => item.id !== id));
      });
      return { previous };
    },
    onError: (_err, _vars, context) => context?.previous?.forEach(([queryKey, data]) => qc.setQueryData(queryKey, data)),
    onSettled: () => qc.invalidateQueries({ queryKey: ['relationship-reviews'] }),
  });
}

export function useDismissRelationshipReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.dismissRelationshipReview(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: keys.relationshipReviews('pending') });
      const previous = qc.getQueriesData<RelationshipReviewItem[]>({ queryKey: keys.relationshipReviews('pending') });
      previous.forEach(([queryKey, data]) => {
        if (!data) return;
        qc.setQueryData(queryKey, data.filter((item) => item.id !== id));
      });
      return { previous };
    },
    onError: (_err, _vars, context) => context?.previous?.forEach(([queryKey, data]) => qc.setQueryData(queryKey, data)),
    onSettled: () => qc.invalidateQueries({ queryKey: ['relationship-reviews'] }),
  });
}

export function useConfirmDocumentRelationship(documentId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.confirmRelationshipReview(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: keys.documentRelationships(documentId) });
      const previous = qc.getQueryData<DocumentRelationshipListItem[]>(keys.documentRelationships(documentId));
      qc.setQueryData<DocumentRelationshipListItem[]>(keys.documentRelationships(documentId), (items = []) =>
        items.map((item) => (item.id === id ? { ...item, status: 'confirmed' } : item)),
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) qc.setQueryData(keys.documentRelationships(documentId), context.previous);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: keys.documentRelationships(documentId) }),
  });
}

export function useDismissDocumentRelationship(documentId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.dismissRelationshipReview(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: keys.documentRelationships(documentId) });
      const previous = qc.getQueryData<DocumentRelationshipListItem[]>(keys.documentRelationships(documentId));
      qc.setQueryData<DocumentRelationshipListItem[]>(keys.documentRelationships(documentId), (items = []) =>
        items.map((item) => (item.id === id ? { ...item, status: 'dismissed' } : item)),
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) qc.setQueryData(keys.documentRelationships(documentId), context.previous);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: keys.documentRelationships(documentId) }),
  });
}

export function useActionItems(state: 'open' | 'completed' | 'dismissed' | '', page = 0, limit = 20) {
  const authReady = useAuthReady();
  return useQuery({
    queryKey: [...keys.actionItems(state || 'all'), page, limit],
    queryFn: () => api.listActionItems(state || undefined, limit, page * limit),
    enabled: authReady,
  });
}

export function useCompleteActionItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.completeActionItem(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ['action-items'] });
      const previous = updatePaginatedQueries<ActionItem>(qc, keys.actionItems('open'), (item) => (item.id === id ? null : item));
      return { previous };
    },
    onError: (_err, _vars, context) => {
      context?.previous?.forEach(([queryKey, data]) => qc.setQueryData(queryKey, data));
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['action-items'] });
      qc.invalidateQueries({ queryKey: keys.actionItemMetrics });
    },
  });
}

export function useDismissActionItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.dismissActionItem(id),
    onMutate: async (id) => {
      await qc.cancelQueries({ queryKey: ['action-items'] });
      const previous = updatePaginatedQueries<ActionItem>(qc, keys.actionItems('open'), (item) => (item.id === id ? null : item));
      return { previous };
    },
    onError: (_err, _vars, context) => {
      context?.previous?.forEach(([queryKey, data]) => qc.setQueryData(queryKey, data));
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['action-items'] });
      qc.invalidateQueries({ queryKey: keys.actionItemMetrics });
    },
  });
}

export function useBulkCompleteActionItems() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ids, note }: { ids: string[]; note?: string }) => api.bulkCompleteActionItems(ids, note),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['action-items'] });
      qc.invalidateQueries({ queryKey: keys.actionItemMetrics });
    },
  });
}

export function useBulkDismissActionItems() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ ids, note }: { ids: string[]; note?: string }) => api.bulkDismissActionItems(ids, note),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['action-items'] });
      qc.invalidateQueries({ queryKey: keys.actionItemMetrics });
    },
  });
}

export function useActionItemMetrics() {
  const authReady = useAuthReady();
  return useQuery({ queryKey: keys.actionItemMetrics, queryFn: api.getActionItemMetrics, enabled: authReady });
}

export function useDocumentIntelligence(documentId: string, enabled = true) {
  const authReady = useAuthReady();
  return useQuery({
    queryKey: keys.documentIntelligence(documentId),
    queryFn: () => api.getDocumentIntelligence(documentId),
    enabled: authReady && !!documentId && enabled,
    retry: (failureCount, error) => {
      if (axios.isAxiosError(error) && error.response?.status === 404) return false;
      return failureCount < 2;
    },
  });
}

export function usePatchDocumentIntelligence(documentId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: Record<string, unknown>) => api.patchDocumentIntelligence(documentId, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.documentIntelligence(documentId) }),
  });
}

export function useApproveDocumentCategory(documentId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.approveDocumentCategory(documentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['document', documentId] });
      qc.invalidateQueries({ queryKey: keys.documents });
      qc.invalidateQueries({ queryKey: keys.search });
      qc.invalidateQueries({ queryKey: keys.suggestions });
      qc.invalidateQueries({ queryKey: keys.facets });
      qc.invalidateQueries({ queryKey: keys.timeline });
      qc.invalidateQueries({ queryKey: keys.insightsOverview });
      qc.invalidateQueries({ queryKey: keys.insightsStructured });
      qc.invalidateQueries({ queryKey: keys.categories });
      qc.invalidateQueries({ queryKey: ['relationship-reviews'] });
      qc.invalidateQueries({ queryKey: keys.documentIntelligence(documentId) });
    },
  });
}

export function useOverrideDocumentCategory(documentId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (categoryId: string) => api.overrideDocumentCategory(documentId, categoryId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['document', documentId] });
      qc.invalidateQueries({ queryKey: keys.documents });
      qc.invalidateQueries({ queryKey: keys.search });
      qc.invalidateQueries({ queryKey: keys.suggestions });
      qc.invalidateQueries({ queryKey: keys.facets });
      qc.invalidateQueries({ queryKey: keys.timeline });
      qc.invalidateQueries({ queryKey: keys.insightsOverview });
      qc.invalidateQueries({ queryKey: keys.insightsStructured });
      qc.invalidateQueries({ queryKey: keys.categories });
      qc.invalidateQueries({ queryKey: ['relationship-reviews'] });
      qc.invalidateQueries({ queryKey: keys.documentIntelligence(documentId) });
    },
  });
}

export function useDocumentActionItems(documentId: string) {
  const authReady = useAuthReady();
  return useQuery({
    queryKey: keys.documentActionItems(documentId),
    queryFn: () => api.listDocumentActionItems(documentId),
    enabled: authReady && !!documentId,
  });
}

export function useDocumentAuditHistory(documentId: string) {
  const authReady = useAuthReady();
  return useQuery({
    queryKey: keys.documentAuditHistory(documentId),
    queryFn: () => api.getDocumentAuditHistory(documentId),
    enabled: authReady && !!documentId,
  });
}

export function useInsightsAccess() {
  const authReady = useAuthReady();
  const subscription = useSubscription();
  const plans = usePlans();
  const currentPlanSlug = subscription.data?.plan.slug;
  const currentPlan = (plans.data ?? []).find((plan) => plan.slug === currentPlanSlug) ?? (plans.data ?? []).find((plan) => plan.is_current);
  const insightsEnabled = Boolean(currentPlan?.features?.insights_enabled);
  return { authReady, insightsEnabled, isLoading: subscription.isLoading || plans.isLoading };
}

export function useInsightsOverview() {
  const { authReady, insightsEnabled } = useInsightsAccess();
  return useQuery({ queryKey: keys.insightsOverview, queryFn: api.getInsightsOverview, enabled: authReady && insightsEnabled });
}

export function useStructuredInsights() {
  const { authReady, insightsEnabled } = useInsightsAccess();
  return useQuery({ queryKey: keys.insightsStructured, queryFn: api.getStructuredInsights, enabled: authReady && insightsEnabled });
}

export function useConnections() {
  const authReady = useAuthReady();
  return useQuery({ queryKey: keys.connections, queryFn: api.listConnections, enabled: authReady });
}


export function useAdminUsers(page=0, limit=20) { const authReady = useAuthReady(); return useQuery({queryKey: keys.adminUsers(page, limit), queryFn: () => api.listAdminUsers(limit, page*limit), enabled: authReady}); }
export function useAdminMetrics() { const authReady = useAuthReady(); return useQuery({queryKey: keys.adminMetrics, queryFn: api.getAdminMetrics, enabled: authReady}); }
export function useAdminProcessingSummary() { const authReady = useAuthReady(); return useQuery({queryKey: keys.adminProcessingSummary, queryFn: api.getAdminProcessingSummary, enabled: authReady}); }
export function useAdminAudit(page=0, limit=20) { const authReady = useAuthReady(); return useQuery({queryKey: keys.adminAudit(page, limit), queryFn: () => api.listAdminAudit(limit, page*limit), enabled: authReady}); }

export function useAdminSubscriptions() { const authReady = useAuthReady(); return useQuery({ queryKey: keys.adminSubscriptions, queryFn: api.listAdminSubscriptions, enabled: authReady }); }
export function useAdminUsageSummary(userId: string) { const authReady = useAuthReady(); return useQuery({ queryKey: keys.adminUsageSummary(userId), queryFn: () => api.getAdminUsageSummary(userId), enabled: authReady && Boolean(userId) }); }
export function useAdminSystemStatus() { const authReady = useAuthReady(); return useQuery({ queryKey: keys.adminSystemStatus, queryFn: api.getAdminSystemStatus, enabled: authReady }); }
export function useAdminUpdateUserPlan() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ userId, plan_slug }: { userId: string; plan_slug: string }) => api.updateAdminUserPlan(userId, plan_slug), onSuccess: () => { qc.invalidateQueries({ queryKey: keys.adminSubscriptions }); qc.invalidateQueries({ queryKey: ['admin-audit'] }); } });
}
export function useAdminUpdateUsageControls() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ userId, usage_credits, limit_overrides }: { userId: string; usage_credits: Record<string, number>; limit_overrides: Record<string, number | null> }) => api.updateAdminUsageControls(userId, usage_credits, limit_overrides), onSuccess: () => qc.invalidateQueries({ queryKey: keys.adminSubscriptions }) });
}
export function useAdminCancelOrDowngrade() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ userId, downgrade_to_plan_slug }: { userId: string; downgrade_to_plan_slug: string }) => api.cancelOrDowngradeAdminSubscription(userId, downgrade_to_plan_slug), onSuccess: () => qc.invalidateQueries({ queryKey: keys.adminSubscriptions }) });
}

export function useUpdateUserRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) => api.updateAdminUserRole(userId, role),
    onMutate: async ({ userId, role }) => {
      await qc.cancelQueries({ queryKey: ['admin-users'] });
      const previous = qc.getQueriesData<{ items: Array<{ id: string; role: string }>; total_count: number; limit: number; offset: number }>({ queryKey: ['admin-users'] });
      previous.forEach(([queryKey, data]) => {
        if (!data) return;
        qc.setQueryData(queryKey, {
          ...data,
          items: data.items.map((item) => (item.id === userId ? { ...item, role } : item)),
        });
      });
      return { previous };
    },
    onError: (_err, _vars, context) => context?.previous?.forEach(([queryKey, data]) => qc.setQueryData(queryKey, data)),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] });
      qc.invalidateQueries({ queryKey: ['admin-audit'] });
      qc.invalidateQueries({ queryKey: keys.adminMetrics });
    },
  });
}


export function useChatbotSettings() { const authReady = useAuthReady(); return useQuery({ queryKey: keys.chatbotSettings, queryFn: api.getChatbotSettings, enabled: authReady }); }
export function useUpdateChatbotSettings() { const qc = useQueryClient(); return useMutation({ mutationFn: api.updateChatbotSettings, onSuccess: () => qc.invalidateQueries({ queryKey: keys.chatbotSettings }) }); }
export function useResetChatbotSettings() { const qc = useQueryClient(); return useMutation({ mutationFn: api.resetChatbotSettings, onSuccess: () => qc.invalidateQueries({ queryKey: keys.chatbotSettings }) }); }
export function useCreateChatSession() { const qc = useQueryClient(); return useMutation({ mutationFn: (title?: string) => api.createChatSession(title), onSuccess: () => qc.invalidateQueries({ queryKey: keys.chatSessions }) }); }
export function useChatSessions() { const authReady = useAuthReady(); return useQuery({ queryKey: keys.chatSessions, queryFn: api.listChatSessions, enabled: authReady }); }
export function useChatSession(sessionId: string) { const authReady = useAuthReady(); return useQuery({ queryKey: keys.chatSession(sessionId), queryFn: () => api.getChatSession(sessionId), enabled: authReady && Boolean(sessionId) }); }
export function useSendChatMessage(sessionId: string) { const qc = useQueryClient(); return useMutation({ mutationFn: (payload: Parameters<typeof api.sendChatMessage>[1]) => api.sendChatMessage(sessionId, payload), onSuccess: () => { qc.invalidateQueries({ queryKey: keys.chatSessions }); qc.invalidateQueries({ queryKey: keys.chatSession(sessionId) }); } }); }
export function useInvalidateChatSession() {
  const qc = useQueryClient();
  return (sessionId: string) => {
    qc.invalidateQueries({ queryKey: keys.chatSessions });
    qc.invalidateQueries({ queryKey: keys.chatSession(sessionId) });
  };
}
export function useReports() { const authReady = useAuthReady(); return useQuery({ queryKey: keys.reports, queryFn: api.listReports, enabled: authReady }); }
export function useReport(reportId: string) { const authReady = useAuthReady(); return useQuery({ queryKey: keys.report(reportId), queryFn: () => api.getReport(reportId), enabled: authReady && Boolean(reportId) }); }
export function useCreateReport() { const qc = useQueryClient(); return useMutation({ mutationFn: api.createReport, onSuccess: () => qc.invalidateQueries({ queryKey: keys.reports }) }); }
export function useUpdateReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ reportId, payload }: { reportId: string; payload: Parameters<typeof api.updateReport>[1] }) => api.updateReport(reportId, payload),
    onSuccess: (report) => {
      qc.setQueryData(keys.report(report.id), report);
      qc.invalidateQueries({ queryKey: keys.reports });
    },
  });
}

export function useGmailPreview() {
  return useMutation({
    mutationFn: api.gmailPreview,
  });
}

export function useGmailImport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.gmailImport,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.documents });
      qc.invalidateQueries({ queryKey: keys.search });
      qc.invalidateQueries({ queryKey: keys.suggestions });
      qc.invalidateQueries({ queryKey: keys.facets });
      qc.invalidateQueries({ queryKey: keys.timeline });
      qc.invalidateQueries({ queryKey: keys.insightsOverview });
      qc.invalidateQueries({ queryKey: keys.insightsStructured });
      qc.invalidateQueries({ queryKey: keys.categories });
      qc.invalidateQueries({ queryKey: ['relationship-reviews'] });
    },
  });
}


export function useAdminPromptTemplates() { const authReady = useAuthReady(); return useQuery({ queryKey: keys.adminPrompts, queryFn: api.listPromptTemplates, enabled: authReady }); }
export function useAdminLlmModels() { const authReady = useAuthReady(); return useQuery({ queryKey: keys.adminLlmModels, queryFn: api.getAdminLlmModels, enabled: authReady }); }

export function useCreatePromptTemplate() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (payload: PromptTemplateCreateRequest) => api.createPromptTemplate(payload), onSuccess: () => qc.invalidateQueries({ queryKey: keys.adminPrompts }) });
}

export function useUpdatePromptTemplate() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: ({ promptId, payload }: { promptId: string; payload: PromptTemplateUpdateRequest }) => api.updatePromptTemplate(promptId, payload), onSuccess: () => qc.invalidateQueries({ queryKey: keys.adminPrompts }) });
}

export function useActivatePromptTemplate() {
  const qc = useQueryClient();
  return useMutation({ mutationFn: (promptId: string) => api.activatePromptTemplate(promptId), onSuccess: () => qc.invalidateQueries({ queryKey: keys.adminPrompts }) });
}


export function useTestPromptTemplate() {
  return useMutation({ mutationFn: (payload: PromptTemplateTestRequest) => api.testPromptTemplate(payload) });
}

export function useUsage() { const authReady = useAuthReady(); return useQuery({ queryKey: keys.usage, queryFn: api.getUsage, enabled: authReady }); }
export function useSubscription() { const authReady = useAuthReady(); return useQuery({ queryKey: keys.subscription, queryFn: api.getSubscription, enabled: authReady }); }
export function usePlans() { const authReady = useAuthReady(); return useQuery({ queryKey: keys.plans, queryFn: api.listPlans, enabled: authReady }); }
export function useCreateCheckoutSession() { return useMutation({ mutationFn: (plan: string) => api.createCheckoutSession(plan) }); }
export function useCreateCustomerPortalSession() { return useMutation({ mutationFn: () => api.createCustomerPortalSession() }); }

export function useAdminPromptExecutions() { const authReady = useAuthReady(); return useQuery({ queryKey: keys.adminPromptExecutions, queryFn: api.listPromptExecutions, enabled: authReady }); }
