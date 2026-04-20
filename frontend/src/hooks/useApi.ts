import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';

export const keys = {
  documents: ['documents'] as const,
  queueStats: ['queue-stats'] as const,
  queueItems: ['queue-items'] as const,
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

export function useCategories() {
  return useQuery({ queryKey: keys.categories, queryFn: api.listCategories });
}

export function useInsightsOverview() {
  return useQuery({ queryKey: ['insights-overview'], queryFn: api.getInsightsOverview });
}

export function useConnections() {
  return useQuery({ queryKey: keys.connections, queryFn: api.listConnections });
}
