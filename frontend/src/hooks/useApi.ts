import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

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
  categories: ['categories'] as const,
  connections: ['connections'] as const,
};

export function useDocuments() {
  return useQuery({ queryKey: keys.documents, queryFn: () => api.listDocuments(false) });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.uploadDocument,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.documents });
    },
  });
}

export function useQueueStats() {
  return useQuery({ queryKey: keys.queueStats, queryFn: api.getQueueStats, refetchInterval: 5000 });
}

export function useQueueItems() {
  return useQuery({ queryKey: keys.queueItems, queryFn: api.getQueueItems, refetchInterval: 5000 });
}

export function useReviewQueue() {
  return useQuery({ queryKey: keys.reviewQueue, queryFn: api.getReviewQueue, refetchInterval: 5000 });
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
    },
  });
}

export function useCategories() {
  return useQuery({ queryKey: keys.categories, queryFn: api.listCategories });
}

export function useReviewItems(status: 'open' | 'resolved' | 'dismissed') {
  return useQuery({ queryKey: keys.reviewItems(status), queryFn: () => api.listReviewItems(status) });
}

export function useResolveReviewItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note?: string }) => api.resolveReviewItem(id, note),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['review-items'] });
      qc.invalidateQueries({ queryKey: keys.reviewMetrics });
    },
  });
}

export function useDismissReviewItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note?: string }) => api.dismissReviewItem(id, note),
    onSuccess: () => {
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

export function useReviewMetrics() {
  return useQuery({ queryKey: keys.reviewMetrics, queryFn: api.getReviewMetrics });
}

export function useRelationshipReviews(status: 'pending' | 'confirmed' | 'dismissed') {
  return useQuery({ queryKey: keys.relationshipReviews(status), queryFn: () => api.listRelationshipReviews(status) });
}

export function useConfirmRelationshipReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.confirmRelationshipReview(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['relationship-reviews'] }),
  });
}

export function useDismissRelationshipReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.dismissRelationshipReview(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['relationship-reviews'] }),
  });
}

export function useActionItems(state: 'open' | 'completed' | 'dismissed' | '') {
  return useQuery({
    queryKey: keys.actionItems(state || 'all'),
    queryFn: () => api.listActionItems(state || undefined),
  });
}

export function useCompleteActionItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.completeActionItem(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['action-items'] });
      qc.invalidateQueries({ queryKey: keys.actionItemMetrics });
    },
  });
}

export function useDismissActionItem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.dismissActionItem(id),
    onSuccess: () => {
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
  return useQuery({ queryKey: keys.actionItemMetrics, queryFn: api.getActionItemMetrics });
}

export function useDocumentIntelligence(documentId: string) {
  return useQuery({ queryKey: keys.documentIntelligence(documentId), queryFn: () => api.getDocumentIntelligence(documentId), enabled: !!documentId });
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
      qc.invalidateQueries({ queryKey: keys.documentIntelligence(documentId) });
    },
  });
}

export function useDocumentActionItems(documentId: string) {
  return useQuery({
    queryKey: keys.documentActionItems(documentId),
    queryFn: () => api.listDocumentActionItems(documentId),
    enabled: !!documentId,
  });
}

export function useDocumentAuditHistory(documentId: string) {
  return useQuery({
    queryKey: keys.documentAuditHistory(documentId),
    queryFn: () => api.getDocumentAuditHistory(documentId),
    enabled: !!documentId,
  });
}

export function useInsightsOverview() {
  return useQuery({ queryKey: ['insights-overview'], queryFn: api.getInsightsOverview });
}

export function useConnections() {
  return useQuery({ queryKey: keys.connections, queryFn: api.listConnections });
}
