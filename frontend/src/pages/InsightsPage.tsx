import { useMemo, useState } from 'react';
import { useInsightsOverview, useStructuredInsights } from '@/hooks/useApi';
import { Card } from '@/components/ui/Card';
import { EmptyState, ErrorState, LoadingState } from '@/components/ui/States';

const TYPE_FILTERS = [
  { label: 'All', value: 'all' },
  { label: 'Risks', value: 'risk' },
  { label: 'Inconsistencies', value: 'inconsistency' },
  { label: 'Changes', value: 'change' },
  { label: 'Missing information', value: 'missing_information' },
  { label: 'Milestones', value: 'milestone' },
] as const;

const SEVERITY_FILTERS = [
  { label: 'All severity', value: 'all' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
  { label: 'Low', value: 'low' },
] as const;

function normalizeFilterValue(value: string) {
  return value.toLowerCase().replace(/\s+/g, '_');
}

export function InsightsPage() {
  const { data, isLoading, isError } = useInsightsOverview();
  const { data: structuredInsights, isLoading: structuredLoading, isError: structuredError } = useStructuredInsights();
  const [typeFilter, setTypeFilter] = useState<(typeof TYPE_FILTERS)[number]['value']>('all');
  const [severityFilter, setSeverityFilter] = useState<(typeof SEVERITY_FILTERS)[number]['value']>('all');

  const filteredInsights = useMemo(() => {
    const insights = structuredInsights ?? [];
    return insights.filter((insight) => {
      const normalizedType = normalizeFilterValue(insight.type);
      const normalizedSeverity = normalizeFilterValue(insight.severity);
      const typeMatch = typeFilter === 'all' || normalizedType === typeFilter;
      const severityMatch = severityFilter === 'all' || normalizedSeverity === severityFilter;
      return typeMatch && severityMatch;
    });
  }, [severityFilter, structuredInsights, typeFilter]);

  const isInitialLoading = isLoading || structuredLoading;
  const hasError = isError || structuredError;
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Insights</h1>
      {isInitialLoading && <LoadingState />}
      {hasError && <ErrorState message="Failed to load insights" />}
      {!isInitialLoading && !hasError && !data && <EmptyState label="No insights available." />}
      {!isInitialLoading && !hasError && (
        <section className="space-y-3" aria-label="Structured insights">
          <h2 className="text-base font-medium">Structured insights</h2>
          {!!structuredInsights?.length && (
            <div className="space-y-2" aria-label="Insight filters">
              <div className="flex flex-wrap gap-2">
                {TYPE_FILTERS.map((filter) => (
                  <button
                    key={filter.value}
                    type="button"
                    onClick={() => setTypeFilter(filter.value)}
                    className={`rounded-full px-3 py-1 text-xs font-medium ${
                      typeFilter === filter.value ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
              <label className="flex w-full max-w-xs flex-col gap-1 text-xs font-medium text-slate-600">
                Severity
                <select
                  className="rounded-md border border-slate-300 bg-white px-2 py-1 text-sm"
                  value={severityFilter}
                  onChange={(event) => setSeverityFilter(event.target.value as (typeof SEVERITY_FILTERS)[number]['value'])}
                  aria-label="Severity filter"
                >
                  {SEVERITY_FILTERS.map((filter) => (
                    <option key={filter.value} value={filter.value}>
                      {filter.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          )}
          {!structuredInsights?.length && <EmptyState label="No structured insights available." />}
          {!!structuredInsights?.length && !filteredInsights.length && <EmptyState label="No insights match the selected filters." />}
          {filteredInsights.map((insight, index) => (
            <Card key={`${insight.type}-${index}`}>
              <div className="space-y-2 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs uppercase tracking-wide">{insight.type}</span>
                  <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs font-medium">Severity: {insight.severity}</span>
                </div>
                <h3 className="text-base font-semibold">{insight.title}</h3>
                <p className="text-slate-700">{insight.description}</p>
                {!!insight.related_documents?.length && (
                  <div>
                    <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Related documents</p>
                    <ul className="space-y-1">
                      {insight.related_documents.map((doc) => (
                        <li key={doc.document_id}>
                          <a className="text-blue-600 underline" href={`/documents/${doc.document_id}`}>
                            {doc.title ?? doc.document_id}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {!!insight.evidence_refs?.length && (
                  <div>
                    <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">Evidence</p>
                    <ul className="list-disc space-y-1 pl-5">
                      {insight.evidence_refs.map((evidence, evidenceIndex) => (
                        <li key={`${evidence.reference ?? 'evidence'}-${evidenceIndex}`}>
                          {[evidence.source, evidence.reference, evidence.quote].filter(Boolean).join(' • ') || 'Evidence reference'}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </section>
      )}
      <Card><h3 className="mb-2">Action Items</h3><pre className="text-xs">{JSON.stringify(data?.action_item_summary ?? {}, null, 2)}</pre></Card>
      <Card><h3 className="mb-2">Category distribution</h3><pre className="text-xs">{JSON.stringify(data?.category_distribution ?? [], null, 2)}</pre></Card>
      <Card><h3 className="mb-2">Recent activity</h3><pre className="text-xs">{JSON.stringify(data?.recent_activity ?? [], null, 2)}</pre></Card>
    </div>
  );
}
