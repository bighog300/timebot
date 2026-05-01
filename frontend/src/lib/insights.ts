import type { StructuredInsight } from '@/types/api';

const SEVERITY_ORDER: Record<string, number> = {
  high: 0,
  medium: 1,
  low: 2,
};

export function normalizeSeverity(severity?: string | null) {
  return (severity ?? '').toLowerCase().trim();
}

export function severityRank(severity?: string | null) {
  const normalizedSeverity = normalizeSeverity(severity);
  return SEVERITY_ORDER[normalizedSeverity] ?? Number.MAX_SAFE_INTEGER;
}

export function sortInsightsBySeverity<T extends Pick<StructuredInsight, 'severity'>>(insights: T[]) {
  return [...insights].sort((a, b) => severityRank(a.severity) - severityRank(b.severity));
}

export function getSeverityBadgeClass(severity?: string | null) {
  const normalizedSeverity = normalizeSeverity(severity);
  if (normalizedSeverity === 'high') return 'bg-rose-100 text-rose-800 border border-rose-300';
  if (normalizedSeverity === 'medium') return 'bg-amber-100 text-amber-800 border border-amber-300';
  if (normalizedSeverity === 'low') return 'bg-emerald-100 text-emerald-800 border border-emerald-300';
  return 'bg-slate-200 text-slate-700 border border-slate-300';
}

export function getSeverityLabel(severity?: string | null) {
  const normalizedSeverity = normalizeSeverity(severity);
  if (!normalizedSeverity) return 'Unknown';
  return normalizedSeverity.charAt(0).toUpperCase() + normalizedSeverity.slice(1);
}
