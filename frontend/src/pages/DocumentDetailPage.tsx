import { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import { api } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { ErrorState, LoadingState, EmptyState } from '@/components/ui/States';
import { ProcessingStatusIndicator } from '@/components/documents/ProcessingStatusIndicator';
import { getSeverityBadgeClass, getSeverityLabel, sortInsightsBySeverity } from '@/lib/insights';
import { useUIStore } from '@/store/uiStore';
import {
  useApproveDocumentCategory,
  useConfirmDocumentRelationship,
  useDismissDocumentRelationship,
  useCategories,
  useDocumentActionItems,
  useDocumentAuditHistory,
  useDocumentIntelligence,
  useDocumentClusters,
  useDocumentRelationships,
  useOverrideDocumentCategory,
  usePatchDocumentIntelligence,
  useStructuredInsights,
} from '@/hooks/useApi';

const IN_FLIGHT_PROCESSING_STAGES = new Set(['queued', 'extracting', 'analyzing', 'enriching', 'embedding']);

function docStatusReady(status?: string) {
  if (!status) return false;
  return status !== 'uploading' && status !== 'processing';
}

export function shouldContinuePolling(data?: { processing_status?: string; processing_stage?: string; enrichment_pending?: boolean; enrichment_status?: string }) {
  if (!data) return false;
  const status = data.processing_status;
  const stage = data.processing_stage;
  const enrichmentPending = Boolean(data.enrichment_pending);
  const processingInFlight =
    status === 'uploading' ||
    status === 'processing' ||
    (typeof stage === 'string' && IN_FLIGHT_PROCESSING_STAGES.has(stage));

  if (processingInFlight || enrichmentPending) return true;

  const processingTerminal = status === 'completed' || status === 'failed';
  const enrichmentCompleteOrDegraded = data.enrichment_status === 'complete' || data.enrichment_status === 'degraded';
  if (processingTerminal && enrichmentCompleteOrDegraded) return false;

  return false;
}

const SIGNAL_LABELS: Record<string, string> = {
  structural_email_thread: 'Same email thread',
  structural_attachment: 'Attachment relationship',
  shared_terms: 'Shared terms',
  timeline_proximity: 'Timeline proximity',
  ai_detected: 'AI detected',
};

function toFriendlySignalLabel(signal: string) {
  return SIGNAL_LABELS[signal] ?? signal;
}

export function DocumentDetailPage() {
  const { id = '' } = useParams();
  const qc = useQueryClient();
  const pushToast = useUIStore((s) => s.pushToast);
  const documentQuery = useQuery({
    queryKey: ['document', id],
    queryFn: () => api.getDocument(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data as { processing_status?: string; processing_stage?: string; enrichment_pending?: boolean; enrichment_status?: string } | undefined;
      return shouldContinuePolling(data) ? 3000 : false;
    },
  });
  const similarQuery = useQuery({ queryKey: ['similar', id], queryFn: () => api.findSimilar(id), enabled: !!id });

  const shouldFetchIntelligence = docStatusReady(documentQuery.data?.processing_status);
  const intelligenceQuery = useDocumentIntelligence(id, shouldFetchIntelligence);
  const categoriesQuery = useCategories();
  const actionItemsQuery = useDocumentActionItems(id);
  const auditQuery = useDocumentAuditHistory(id);
  const relationshipsQuery = useDocumentRelationships(id);
  const clustersQuery = useDocumentClusters();
  const structuredInsightsQuery = useStructuredInsights();
  const confirmRelationship = useConfirmDocumentRelationship(id);
  const dismissRelationship = useDismissDocumentRelationship(id);
  const patchIntelligence = usePatchDocumentIntelligence(id);
  const approveCategory = useApproveDocumentCategory(id);
  const overrideCategory = useOverrideDocumentCategory(id);

  const [summaryDraft, setSummaryDraft] = useState('');
  const [tagsDraft, setTagsDraft] = useState('');
  const [keyPointsDraft, setKeyPointsDraft] = useState('');
  const [categoryOverrideId, setCategoryOverrideId] = useState('');
  const [relationshipFilter, setRelationshipFilter] = useState<'all' | 'structural' | 'ai_detected' | 'confirmed' | 'pending'>('all');

  useEffect(() => {
    if (!intelligenceQuery.data) return;
    setSummaryDraft(intelligenceQuery.data.summary ?? '');
    setTagsDraft(intelligenceQuery.data.suggested_tags.join(', '));
    setKeyPointsDraft(intelligenceQuery.data.key_points.join('\n'));
  }, [intelligenceQuery.data]);

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['document', id] });
    qc.invalidateQueries({ queryKey: ['documents'] });
    qc.invalidateQueries({ queryKey: ['intelligence', id] });
    qc.invalidateQueries({ queryKey: ['timeline'] });
    qc.invalidateQueries({ queryKey: ['search'] });
    qc.invalidateQueries({ queryKey: ['action-items'] });
    qc.invalidateQueries({ queryKey: ['relationships'] });
  };

  const updateMutation = useMutation({
    mutationFn: (patch: Record<string, unknown>) => api.updateDocument(id, patch),
    onSuccess: () => {
      refresh();
      pushToast('Document updated');
    },
    onError: () => pushToast('Failed to update document'),
  });
  const reprocessMutation = useMutation({
    mutationFn: () => api.reprocessDocument(id),
    onSuccess: () => {
      refresh();
      pushToast('Reprocessing queued');
    },
    onError: (error: unknown) => {
      const message = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      pushToast(message ? `Failed to queue reprocessing: ${message}` : 'Failed to queue reprocessing');
    },
  });
  const deleteMutation = useMutation({
    mutationFn: () => api.deleteDocument(id),
    onSuccess: () => {
      refresh();
      qc.invalidateQueries({ queryKey: ['insights-structured'] });
      qc.invalidateQueries({ queryKey: ['document-clusters'] });
      pushToast('Document deleted');
      window.location.href = '/documents';
    },
    onError: () => pushToast('Failed to delete document'),
  });

  const filteredRelationships = useMemo(() => {
    const relationships = relationshipsQuery.data ?? [];
    return relationships.filter((item) => {
      if (relationshipFilter === 'all') return true;
      if (relationshipFilter === 'structural') return item.relationship_type === 'thread' || item.relationship_type === 'attachment';
      if (relationshipFilter === 'confirmed') return item.status === 'confirmed';
      if (relationshipFilter === 'pending') return item.status === 'pending';
      const signals = item.explanation_metadata?.signals ?? [];
      const effectiveConfidence = item.explanation_metadata?.confidence ?? item.confidence;
      return item.relationship_type !== 'thread' && item.relationship_type !== 'attachment' && (signals.length > 0 || effectiveConfidence != null);
    });
  }, [relationshipFilter, relationshipsQuery.data]);

  const relationshipGroups = {
    thread: filteredRelationships.filter((item) => item.relationship_type === 'thread'),
    attachment: filteredRelationships.filter((item) => item.relationship_type === 'attachment'),
    related: filteredRelationships.filter((item) => item.relationship_type !== 'thread' && item.relationship_type !== 'attachment'),
  };
  const currentDocumentClusterId = useMemo(() => {
    const clusters = clustersQuery.data ?? [];
    return clusters.find((cluster) => cluster.document_ids.includes(id))?.cluster_id ?? null;
  }, [clustersQuery.data, id]);
  const renderRelationshipItem = (item: (typeof relationshipGroups)['related'][number]) => (
    <li key={item.id} className="rounded border border-slate-800 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Link className="font-medium text-blue-300 hover:text-blue-200" to={`/documents/${item.related_document_id}`}>
          {item.related_document_title || item.related_document_name || item.related_document_id}
        </Link>
        <span className="rounded bg-slate-800 px-2 py-1 text-xs">{item.relationship_type}</span>
        <span className="rounded bg-slate-800 px-2 py-1 text-xs">{item.status}</span>
        <span className="text-xs text-slate-400">{(item.explanation_metadata?.confidence ?? item.confidence) != null ? `${Math.round((item.explanation_metadata?.confidence ?? item.confidence ?? 0) * 100)}% confidence` : 'n/a confidence'}</span>
      </div>
      <p className="mt-2 break-words text-slate-300">{item.related_document_snippet || 'No summary/snippet available.'}</p>
      {item.explanation_metadata && (item.explanation_metadata.reason || (item.explanation_metadata.signals?.length ?? 0) > 0) && (
        <p className="mt-2 text-xs text-slate-400">
          <span className="font-medium text-slate-300">Why related:</span>{' '}
          {item.explanation_metadata.reason || 'Similarity signals detected.'}
        </p>
      )}
      {item.explanation_metadata && (
        <details className="mt-2 rounded border border-slate-800 p-2 text-xs text-slate-300" data-testid="why-related-details">
          <summary className="cursor-pointer list-none font-medium text-slate-200">
            <span className="inline-flex items-center gap-1">
              <span aria-hidden>▸</span>
              Why related details
            </span>
          </summary>
            <div className="mt-2 space-y-2 break-words leading-relaxed">
            {item.explanation_metadata.reason && (
              <p>
                <span className="font-medium text-slate-200">Reason:</span> {item.explanation_metadata.reason}
              </p>
            )}
            {(item.explanation_metadata.confidence ?? item.confidence) != null && (
              <p>
                <span className="font-medium text-slate-200">Confidence:</span>{' '}
                {Math.round(((item.explanation_metadata.confidence ?? item.confidence) ?? 0) * 100)}%
              </p>
            )}
            {(item.explanation_metadata.signals?.length ?? 0) > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {item.explanation_metadata.signals?.map((signal) => (
                  <span className="rounded bg-slate-800 px-2 py-1 text-[11px]" key={signal}>
                    {toFriendlySignalLabel(signal)}
                  </span>
                ))}
              </div>
            )}
          </div>
        </details>
      )}
      {currentDocumentClusterId && (
        <div className="mt-2">
          <Link
            className="text-xs text-blue-300 hover:text-blue-200 hover:underline"
            to={`/documents?cluster=${encodeURIComponent(currentDocumentClusterId)}`}
          >
            View related cluster
          </Link>
        </div>
      )}
      {item.status === 'pending' && item.relationship_type !== 'thread' && item.relationship_type !== 'attachment' && (
        <div className="mt-3 grid grid-cols-2 gap-2 sm:flex sm:flex-wrap" data-testid="relationship-actions">
          <Button
            className="min-h-10 bg-emerald-700 hover:bg-emerald-600"
            disabled={confirmRelationship.isPending || dismissRelationship.isPending}
            onClick={() => confirmRelationship.mutate(item.id, { onError: () => pushToast('Failed to confirm relationship') })}
          >
            Confirm
          </Button>
          <Button
            className="min-h-10 bg-slate-700 hover:bg-slate-600"
            disabled={confirmRelationship.isPending || dismissRelationship.isPending}
            onClick={() => dismissRelationship.mutate(item.id, { onError: () => pushToast('Failed to reject relationship') })}
          >
            Reject
          </Button>
        </div>
      )}
    </li>
  );
  const documentInsights = useMemo(() => {
    const insights = structuredInsightsQuery.data ?? [];
    return sortInsightsBySeverity(insights.filter((insight) => insight.related_documents?.some((docRef) => docRef.document_id === id)));
  }, [id, structuredInsightsQuery.data]);

  if (documentQuery.isLoading) return <LoadingState />;
  if (documentQuery.isError || !documentQuery.data) return <ErrorState message="Document not found" />;

  const doc = documentQuery.data;
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">{doc.filename}</h1>
      <ProcessingStatusIndicator
        status={doc.processing_stage || doc.processing_status}
        processingError={doc.processing_error}
        progress={doc.processing_progress}
        message={doc.processing_message}
        showErrorBanner
      />
      {doc.processing_status === "completed" && doc.enrichment_pending && (
        <Card>Analysis complete. Final enrichment is still running.</Card>
      )}
      {doc.ai_analysis_degraded && (
        <Card>Analysis completed with partial AI output.</Card>
      )}
      {Array.isArray(doc.intelligence_warnings) && doc.intelligence_warnings.length > 0 && (
        <Card>
          <h2 className="mb-2 text-sm font-semibold text-amber-300">Intelligence warnings</h2>
          <ul className="space-y-1 text-sm text-amber-100" data-testid="intelligence-warnings">
            {doc.intelligence_warnings.map((warning, index) => (
              <li className="break-words" key={`${warning}-${index}`}>
                • {warning}
              </li>
            ))}
          </ul>
        </Card>
      )}
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => updateMutation.mutate({ is_favorite: !doc.is_favorite })}>{doc.is_favorite ? 'Unfavorite' : 'Favorite'}</Button>
        <Button onClick={() => updateMutation.mutate({ is_archived: !doc.is_archived })}>{doc.is_archived ? 'Unarchive' : 'Archive'}</Button>
        <Button onClick={() => reprocessMutation.mutate()}>Reprocess</Button>
        <Button
          className="bg-red-700 hover:bg-red-600"
          onClick={() => {
            if (window.confirm('Delete this document permanently?')) {
              deleteMutation.mutate();
            }
          }}
        >
          Delete
        </Button>
      </div>

      <Card>
        <h2 className="mb-2 text-lg">Document intelligence</h2>
        {!shouldFetchIntelligence && (
          <EmptyState label={doc.processing_error ? `Processing failed: ${doc.processing_error}` : 'Document is still processing. Intelligence is not available yet.'} />
        )}
        {shouldFetchIntelligence && intelligenceQuery.isLoading && <LoadingState label="Loading intelligence..." />}
        {shouldFetchIntelligence && intelligenceQuery.isError && (
          <ErrorState
            message={doc.processing_error ?? 'AI enrichment is unavailable for this document. Configure OPENAI_API_KEY and reprocess to generate intelligence.'}
          />
        )}
        {shouldFetchIntelligence && intelligenceQuery.isSuccess && !intelligenceQuery.data && (
          <EmptyState label={(doc.summary && doc.summary.trim()) ? doc.summary : "Intelligence is not available yet."} />
        )}
        {shouldFetchIntelligence && intelligenceQuery.data && (
          <div className="space-y-3">
            <div className="text-sm text-slate-300">Confidence: <span className="font-medium">{intelligenceQuery.data.confidence}</span></div>
            <div className="text-sm text-slate-300">Suggested category: <span className="font-medium">{doc.ai_category?.name ?? 'None'}</span></div>
            <textarea className="w-full rounded border border-slate-700 bg-slate-950 p-2 text-sm" value={summaryDraft} onChange={(e) => setSummaryDraft(e.target.value)} rows={4} />
            <textarea className="w-full rounded border border-slate-700 bg-slate-950 p-2 text-sm" value={keyPointsDraft} onChange={(e) => setKeyPointsDraft(e.target.value)} rows={4} />
            <input className="w-full rounded border border-slate-700 bg-slate-950 p-2 text-sm" value={tagsDraft} onChange={(e) => setTagsDraft(e.target.value)} />
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() =>
                  patchIntelligence.mutate({
                    summary: summaryDraft,
                    key_points: keyPointsDraft.split('\n').map((v) => v.trim()).filter(Boolean),
                    suggested_tags: tagsDraft.split(',').map((v) => v.trim()).filter(Boolean),
                  })
                }
              >
                Save intelligence edits
              </Button>
              <Button className="bg-emerald-700 hover:bg-emerald-600" onClick={() => approveCategory.mutate()}>Approve category</Button>
              <select className="rounded border border-slate-700 bg-slate-950 px-2 py-2 text-sm" value={categoryOverrideId} onChange={(e) => setCategoryOverrideId(e.target.value)}>
                <option value="">Select category override</option>
                {(categoriesQuery.data ?? []).map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </select>
              <Button disabled={!categoryOverrideId} onClick={() => overrideCategory.mutate(categoryOverrideId)}>Override category</Button>
            </div>
            <div>
              <h3 className="mb-2 font-medium">Key points</h3>
              <ul className="list-disc space-y-1 pl-5 text-sm">{intelligenceQuery.data.key_points.map((point) => <li key={point}>{point}</li>)}</ul>
            </div>
            <div>
              <h3 className="mb-2 font-medium">Tags</h3>
              <div className="flex flex-wrap gap-2">{intelligenceQuery.data.suggested_tags.map((tag) => <span className="rounded bg-slate-800 px-2 py-1 text-xs" key={tag}>{tag}</span>)}</div>
            </div>
            <div>
              <h3 className="mb-2 font-medium">Entities</h3>
              <pre className="overflow-auto text-xs text-slate-300">{JSON.stringify(intelligenceQuery.data.entities ?? {}, null, 2)}</pre>
            </div>
          </div>
        )}
        {shouldFetchIntelligence && intelligenceQuery.data && !(intelligenceQuery.data.summary?.trim()) && (
          <div className="text-sm text-slate-300">
            {doc.summary?.trim() || "No summary available yet"}
          </div>
        )}
      </Card>

      <div className="grid gap-3 md:grid-cols-2">
        <Card>
          <h3 className="mb-2">Document action items</h3>
          {actionItemsQuery.isLoading && <LoadingState label="Loading action items..." />}
          {actionItemsQuery.isError && <ErrorState message="Failed to load action items." />}
          {actionItemsQuery.isSuccess && (actionItemsQuery.data?.length ?? 0) === 0 && <EmptyState label="No action items." />}
          <ul className="list-disc space-y-1 pl-5 text-sm">{(actionItemsQuery.data ?? []).map((item) => <li key={item.id}>{item.content} ({item.state})</li>)}</ul>
        </Card>
        <Card>
          <h3 className="mb-2">Review audit history</h3>
          {auditQuery.isLoading && <LoadingState label="Loading audit history..." />}
          {auditQuery.isError && <ErrorState message="Failed to load audit history." />}
          {auditQuery.isSuccess && (auditQuery.data?.length ?? 0) === 0 && <EmptyState label="No audit events." />}
          <ul className="space-y-2 text-sm">
            {(auditQuery.data ?? []).map((event) => (
              <li key={event.id} className="rounded border border-slate-800 p-2">{event.event_type} · {new Date(event.created_at).toLocaleString()}</li>
            ))}
          </ul>
        </Card>
      </div>

      <Card>
        <h3 className="mb-2">Insights for this document</h3>
        {structuredInsightsQuery.isLoading && <LoadingState label="Loading insights..." />}
        {structuredInsightsQuery.isError && <ErrorState message="Failed to load insights for this document." />}
        {structuredInsightsQuery.isSuccess && documentInsights.length === 0 && <EmptyState label="No insights found for this document." />}
        {structuredInsightsQuery.isSuccess && documentInsights.length > 0 && (
          <ul className="space-y-2 text-sm">
            {documentInsights.map((insight, index) => (
              <li key={`${insight.type}-${insight.title}-${index}`} className="rounded border border-slate-800 p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded bg-slate-800 px-2 py-1 text-xs">{insight.type}</span>
                  <span className={`rounded px-2 py-1 text-xs ${getSeverityBadgeClass(insight.severity)}`}>Severity: {getSeverityLabel(insight.severity)}</span>
                </div>
                <h4 className="mt-2 font-medium">{insight.title}</h4>
                <p className="mt-1 text-slate-300">{insight.description}</p>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card>
        <h3 className="mb-2">Related documents</h3>
        {(doc.processing_status === 'uploading' || doc.processing_status === 'processing') && (
          <div className="mb-3 text-xs text-slate-400">Relationships may appear after processing completes.</div>
        )}
        {relationshipsQuery.isLoading && <LoadingState label="Loading related documents..." />}
        {relationshipsQuery.isError && <ErrorState message={`Failed to load related documents: ${relationshipsQuery.error.message}`} />}
        {relationshipsQuery.isSuccess && (relationshipsQuery.data?.length ?? 0) === 0 && (
          <EmptyState
            label={
              doc.enrichment_pending
                ? 'Relationship enrichment is still running. Related documents will appear when ready.'
                : 'No related documents found.'
            }
          />
        )}
        {relationshipsQuery.isSuccess && (relationshipsQuery.data?.length ?? 0) > 0 && (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap sm:items-center" role="group" aria-label="Relationship filters" data-testid="relationship-filters">
              <Button className={`w-full ${relationshipFilter === 'all' ? '' : 'bg-slate-700 hover:bg-slate-600'}`} onClick={() => setRelationshipFilter('all')}>All</Button>
              <Button className={`w-full ${relationshipFilter === 'structural' ? '' : 'bg-slate-700 hover:bg-slate-600'}`} onClick={() => setRelationshipFilter('structural')}>Structural</Button>
              <Button className={`w-full ${relationshipFilter === 'ai_detected' ? '' : 'bg-slate-700 hover:bg-slate-600'}`} onClick={() => setRelationshipFilter('ai_detected')}>AI-detected</Button>
              <Button className={`w-full ${relationshipFilter === 'confirmed' ? '' : 'bg-slate-700 hover:bg-slate-600'}`} onClick={() => setRelationshipFilter('confirmed')}>Confirmed</Button>
              <Button className={`col-span-2 w-full sm:col-span-1 ${relationshipFilter === 'pending' ? '' : 'bg-slate-700 hover:bg-slate-600'}`} onClick={() => setRelationshipFilter('pending')}>Pending</Button>
            </div>
            <div>
              <h4 className="mb-2 font-medium">Email Thread</h4>
              {relationshipGroups.thread.length === 0 ? <EmptyState label="No email thread relationships." /> : <ul className="space-y-2">{relationshipGroups.thread.map(renderRelationshipItem)}</ul>}
            </div>
            <div>
              <h4 className="mb-2 font-medium">Attachments</h4>
              {relationshipGroups.attachment.length === 0 ? <EmptyState label="No attachment relationships." /> : <ul className="space-y-2">{relationshipGroups.attachment.map(renderRelationshipItem)}</ul>}
            </div>
            <div>
              <h4 className="mb-2 font-medium">Related Documents</h4>
              {relationshipGroups.related.length === 0 ? <EmptyState label="No AI-detected related documents." /> : <ul className="space-y-2">{relationshipGroups.related.map(renderRelationshipItem)}</ul>}
            </div>
          </div>
        )}
        <div className="mt-2 text-xs text-slate-400">Need to review or update relationships? Visit the <Link to="/review/relationships" className="text-blue-300 hover:text-blue-200">Relationships review page</Link>.</div>
      </Card>

      <Card>
        <h3 className="mb-2">Similar documents</h3>
        {similarQuery.isLoading && <LoadingState label="Loading similar documents..." />}
        {similarQuery.isError && <ErrorState message="Failed to load similar documents" />}
        {similarQuery.isSuccess && (similarQuery.data?.results.length ?? 0) === 0 && <EmptyState label="No similar documents found." />}
        <ul className="space-y-1 text-sm text-slate-300">
          {similarQuery.data?.results.map((row) => <li key={row.document.id}>{row.document.filename} ({row.similarity_score.toFixed(2)})</li>)}
        </ul>
      </Card>
    </div>
  );
}
