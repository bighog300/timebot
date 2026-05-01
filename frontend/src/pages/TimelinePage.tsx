import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { TimelineEvent } from '@/types/api';

type NormalizedTimelineEvent = {
  event: TimelineEvent;
  start: Date;
  end: Date;
  isMilestone: boolean;
};

const formatConfidence = (confidence?: number | null) => {
  if (typeof confidence !== 'number' || Number.isNaN(confidence)) return null;
  return `${Math.round(confidence * 100)}%`;
};

const getTimelineUncertaintyLabel = (event: TimelineEvent): string | null => {
  const precisionRaw = typeof event.date_precision === 'string' ? event.date_precision.trim().toLowerCase() : '';
  const meta = event.metadata && typeof event.metadata === 'object' ? event.metadata : null;
  const metadataFlag = (key: string) => {
    if (!meta) return false;
    const value = meta[key];
    return value === true || value === 'true';
  };

  if (precisionRaw === 'day' || precisionRaw === 'exact') return 'Exact date';
  if (precisionRaw === 'month' || precisionRaw === 'month_only') return 'Month only';
  if (precisionRaw === 'approximate' || precisionRaw === 'approx' || precisionRaw === 'estimated') return 'Approximate date';
  if (precisionRaw === 'uncertain' || precisionRaw === 'unknown') return 'Date uncertain';

  if (metadataFlag('is_approximate') || metadataFlag('approximate_date') || metadataFlag('estimated_date')) return 'Approximate date';
  if (metadataFlag('is_uncertain') || metadataFlag('date_uncertain') || metadataFlag('uncertain_date')) return 'Date uncertain';
  if (metadataFlag('month_only') || metadataFlag('date_month_only')) return 'Month only';

  return null;
};
type TimelineEventGroup = {
  normalizedKey: string;
  primary: NormalizedTimelineEvent;
  events: NormalizedTimelineEvent[];
};

const MS_PER_DAY = 86_400_000;
const LABEL_WIDTH = 320;
const ROW_HEIGHT = 64;
const MAX_CHART_WIDTH = 3600;
const MIN_BAR_WIDTH = 6;

type TimelineZoom = 'fit' | 'month' | 'quarter' | 'year';

const ZOOM_OPTIONS: Array<{ mode: TimelineZoom; label: string }> = [
  { mode: 'fit', label: 'Fit' },
  { mode: 'month', label: 'Month' },
  { mode: 'quarter', label: 'Quarter' },
  { mode: 'year', label: 'Year' },
];

export function TimelinePage() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery({ queryKey: ['timeline'], queryFn: api.getTimeline });
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const [containerWidth, setContainerWidth] = useState<number>(0);
  const [zoomMode, setZoomMode] = useState<TimelineZoom>('fit');
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const updateWidth = () => setContainerWidth(container.clientWidth);
    updateWidth();

    const observer = new ResizeObserver(updateWidth);
    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  const normalizedEvents = useMemo(() => {
    const events = data?.events ?? [];
    return events
      .map<NormalizedTimelineEvent | null>((event) => {
        const startRaw = event.start_date || event.date;
        const endRaw = event.end_date || event.date;
        if (!startRaw || !endRaw) return null;

        const start = new Date(startRaw);
        const end = new Date(endRaw);
        if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;

        return {
          event,
          start,
          end: end < start ? start : end,
          isMilestone: Boolean(event.is_milestone),
        };
      })
      .filter((item): item is NormalizedTimelineEvent => Boolean(item));
  }, [data?.events]);

  const groupedEvents = useMemo(() => {
    const normalizeEventText = (value: string) =>
      value
        .toLowerCase()
        .replace(/[^\w\s]|_/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();

    const groups = new Map<string, TimelineEventGroup>();
    normalizedEvents.forEach((eventItem, idx) => {
      const normalizedKey = normalizeEventText(eventItem.event.title || `event-${idx}`);
      const existing = groups.get(normalizedKey);
      if (existing) {
        existing.events.push(eventItem);
        return;
      }
      groups.set(normalizedKey, { normalizedKey, primary: eventItem, events: [eventItem] });
    });

    return Array.from(groups.values());
  }, [normalizedEvents]);
  const gaps = data?.gaps ?? [];

  const chart = useMemo(() => {
    if (!normalizedEvents.length) return null;

    const minStart = normalizedEvents.reduce((min, item) => (item.start < min ? item.start : min), normalizedEvents[0].start);
    const maxEnd = normalizedEvents.reduce((max, item) => (item.end > max ? item.end : max), normalizedEvents[0].end);

    const spanDays = Math.max(1, Math.ceil((maxEnd.getTime() - minStart.getTime()) / MS_PER_DAY));
    const paddingDays = Math.max(7, Math.ceil(spanDays * 0.05));

    const paddedMin = new Date(minStart);
    paddedMin.setUTCDate(paddedMin.getUTCDate() - paddingDays);
    const paddedMax = new Date(maxEnd);
    paddedMax.setUTCDate(paddedMax.getUTCDate() + paddingDays);

    const totalDays = Math.max(1, Math.ceil((paddedMax.getTime() - paddedMin.getTime()) / MS_PER_DAY));
    const availableTimelineWidth = Math.max(320, (containerWidth || 0) - LABEL_WIDTH);
    const pixelsPerDayByZoom: Record<Exclude<TimelineZoom, 'fit'>, number> = {
      month: 8,
      quarter: 3,
      year: 1,
    };

    const rawWidthByZoom = {
      fit: availableTimelineWidth,
      month: totalDays * pixelsPerDayByZoom.month,
      quarter: totalDays * pixelsPerDayByZoom.quarter,
      year: totalDays * pixelsPerDayByZoom.year,
    } satisfies Record<TimelineZoom, number>;

    const width =
      zoomMode === 'fit'
        ? availableTimelineWidth
        : Math.max(availableTimelineWidth, Math.min(rawWidthByZoom[zoomMode], MAX_CHART_WIDTH));

    const ticks: Array<{ label: string; x: number }> = [];
    const tickDate = new Date(Date.UTC(paddedMin.getUTCFullYear(), paddedMin.getUTCMonth(), 1));
    while (tickDate <= paddedMax) {
      const x = ((tickDate.getTime() - paddedMin.getTime()) / (paddedMax.getTime() - paddedMin.getTime())) * width;
      ticks.push({ label: tickDate.toLocaleDateString(undefined, { month: 'short', year: 'numeric' }), x });
      tickDate.setUTCMonth(tickDate.getUTCMonth() + 1);
    }

    const dateToX = (date: Date) => ((date.getTime() - paddedMin.getTime()) / (paddedMax.getTime() - paddedMin.getTime())) * width;

    return { width, ticks, dateToX, availableTimelineWidth, isScrollable: width > availableTimelineWidth + 8 };
  }, [containerWidth, normalizedEvents, zoomMode]);

  useEffect(() => {
    const scrollEl = scrollContainerRef.current;
    if (!scrollEl) return;
    if (typeof scrollEl.scrollTo === 'function') {
      scrollEl.scrollTo({ left: 0, behavior: 'smooth' });
      return;
    }
    scrollEl.scrollLeft = 0;
  }, [zoomMode]);

  const panTimeline = (direction: 'left' | 'right') => {
    const scrollEl = scrollContainerRef.current;
    if (!scrollEl) return;
    const distance = Math.max(180, Math.floor(scrollEl.clientWidth * 0.7));
    scrollEl.scrollBy({ left: direction === 'left' ? -distance : distance, behavior: 'smooth' });
  };

  if (isLoading) return <div>Loading timeline…</div>;
  if (isError) return <div>Failed to load timeline.</div>;
  if (!groupedEvents.length) return <div>No extracted timeline events yet. Upload documents with dated events or regenerate intelligence.</div>;
  if (!chart) return null;

  return (
    <div className="w-full min-w-0 max-w-[calc(100vw-2rem)] space-y-3 overflow-hidden">
      <h1 className="text-xl font-semibold">Timeline</h1>
      <div className="flex flex-wrap items-center gap-2">
        {ZOOM_OPTIONS.map((option) => (
          <button
            key={option.mode}
            type="button"
            onClick={() => setZoomMode(option.mode)}
            className={`rounded-md border px-3 py-1 text-xs ${zoomMode === option.mode ? 'border-blue-400 bg-blue-500/20 text-blue-200' : 'border-slate-600 text-slate-300 hover:bg-slate-800'}`}
            aria-pressed={zoomMode === option.mode}
          >
            {option.label}
          </button>
        ))}
        {chart.isScrollable ? (
          <>
            <button
              type="button"
              className="rounded-md border border-slate-600 px-2 py-1 text-xs text-slate-300 hover:bg-slate-800"
              onClick={() => panTimeline('left')}
              aria-label="Pan timeline left"
            >
              ←
            </button>
            <button
              type="button"
              className="rounded-md border border-slate-600 px-2 py-1 text-xs text-slate-300 hover:bg-slate-800"
              onClick={() => panTimeline('right')}
              aria-label="Pan timeline right"
            >
              →
            </button>
          </>
        ) : null}
      </div>
      {chart.isScrollable ? <p className="text-xs text-slate-400">Drag or scroll inside the chart to pan timeline.</p> : null}
      {gaps.length ? (
        <div className="rounded-lg border border-slate-700 bg-slate-900/70 px-3 py-2">
          <div className="space-y-1">
            {gaps.map((gap, idx) => (
              <p key={`${gap.start_date}-${gap.end_date}-${idx}`} className="text-xs text-slate-300">
                No activity for {gap.gap_duration_days} days ({gap.start_date} → {gap.end_date})
              </p>
            ))}
          </div>
        </div>
      ) : null}
      <div className="w-full max-w-full min-w-0 overflow-hidden rounded-2xl border border-slate-700 bg-slate-900 shadow-sm" data-testid="timeline-card">
        <div
          ref={scrollContainerRef}
          className="timeline-scroll w-full max-w-full min-w-0 max-h-[calc(100vh-240px)] overflow-auto overscroll-contain"
          style={{ WebkitOverflowScrolling: 'touch', touchAction: 'pan-x pan-y' }}
          data-testid="timeline-scroll-container"
        >
          <div className="relative" style={{ width: LABEL_WIDTH + chart.width, maxWidth: 'none' }} data-testid="timeline-inner-content">
            <div className="sticky top-0 z-20 flex border-b border-slate-700 bg-slate-900/95">
              <div
                className="sticky left-0 top-0 z-40 shrink-0 border-r border-slate-700 bg-slate-900 p-3 text-xs font-semibold uppercase tracking-wide text-slate-300"
                style={{ width: LABEL_WIDTH }}
              >
              Event / Document
              </div>
              <div className="relative shrink-0" style={{ width: chart.width, height: 44 }} data-testid="timeline-axis">
                {chart.ticks.map((tick) => (
                  <div key={tick.label} className="absolute inset-y-0" style={{ left: tick.x }}>
                    <div className="h-3 w-px bg-slate-500" />
                    <div className="mt-1 -translate-x-1/2 whitespace-nowrap text-xs text-slate-300">{tick.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {groupedEvents.map((group, idx) => {
              const item = group.primary;
              const startX = chart.dateToX(item.start);
              const endX = chart.dateToX(item.end);
              const width = Math.max(MIN_BAR_WIDTH, endX - startX);
              const similarCount = group.events.length - 1;
              const isExpanded = Boolean(expandedGroups[group.normalizedKey]);
              const distinctDocuments = new Set(group.events.map((source) => source.event.document_id));
              const groupMaxConfidence = group.events.reduce<number | null>((max, sourceEvent) => {
                const value = sourceEvent.event.confidence;
                if (typeof value !== 'number' || Number.isNaN(value)) return max;
                return max === null ? value : Math.max(max, value);
              }, null);
              const primaryConfidenceLabel = formatConfidence(group.events.length > 1 ? groupMaxConfidence : item.event.confidence);
              const categoryLabel = item.event.category?.trim() || null;
              const uncertaintyLabel = getTimelineUncertaintyLabel(item.event);

              return (
                <div
                  key={`${group.normalizedKey}-${item.event.document_id}-${idx}`}
                  className="flex w-full min-w-0 cursor-pointer border-b border-slate-700 text-left hover:bg-slate-800/60"
                  onClick={() => navigate(`/documents/${item.event.document_id}`)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      navigate(`/documents/${item.event.document_id}`);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  title={`${item.event.title} • ${item.event.document_title} • ${item.event.start_date || item.event.date}${item.event.end_date ? ` → ${item.event.end_date}` : ''}${item.event.source_quote ? ` • ${item.event.source_quote}` : ''}`}
                >
                  <div className="sticky left-0 z-30 shrink-0 border-r border-slate-700 bg-slate-900 p-3" style={{ width: LABEL_WIDTH }}>
                    <div className="truncate text-sm font-medium">{item.event.title}</div>
                    <div className="truncate text-xs text-slate-400">{item.event.document_title}</div>
                    {categoryLabel ? <div className="truncate text-[11px] text-slate-500">Type: {categoryLabel}</div> : null}
                    {primaryConfidenceLabel ? <div className="text-xs text-slate-500">Confidence: {primaryConfidenceLabel}</div> : null}
                    {item.event.is_milestone ? (
                      <span className="mt-1 inline-flex rounded-full border border-emerald-500/60 bg-emerald-500/10 px-2 py-0.5 text-[11px] text-emerald-200">
                        Milestone
                      </span>
                    ) : null}
                    {uncertaintyLabel ? (
                      <span className="mt-1 inline-flex max-w-full rounded-full border border-amber-600/60 bg-amber-500/10 px-2 py-0.5 text-[11px] text-amber-200">
                        {uncertaintyLabel}
                      </span>
                    ) : null}
                    {group.events.length > 1 ? (
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <span className="text-xs text-slate-400">{group.events.length} events</span>
                        <span className="text-xs text-slate-400">{distinctDocuments.size} documents</span>
                        <span className="text-xs text-slate-500">+{similarCount} similar events</span>
                        <button
                          type="button"
                          className="rounded border border-slate-600 px-2 py-0.5 text-[11px] text-slate-300 hover:bg-slate-800"
                          onClick={(e) => {
                            e.stopPropagation();
                            setExpandedGroups((prev) => ({ ...prev, [group.normalizedKey]: !prev[group.normalizedKey] }));
                          }}
                          aria-expanded={isExpanded}
                        >
                          {isExpanded ? 'Hide' : 'Show'}
                        </button>
                      </div>
                    ) : null}
                    {isExpanded ? (
                      <ul className="mt-2 space-y-1 text-xs text-slate-400">
                        {group.events.map((sourceEvent, sourceIdx) => {
                          const sourceUncertaintyLabel = getTimelineUncertaintyLabel(sourceEvent.event);
                          return (
                          <li key={`${sourceEvent.event.document_id}-${sourceIdx}`} className="space-y-0.5">
                            <div className="truncate">{sourceEvent.event.document_title}: {sourceEvent.event.start_date || sourceEvent.event.date}</div>
                            <div className="truncate text-[11px] text-slate-500">
                              {sourceEvent.event.category ? `Type: ${sourceEvent.event.category} • ` : ''}
                              {sourceEvent.event.source ? `Source: ${sourceEvent.event.source} • ` : ''}
                              {formatConfidence(sourceEvent.event.confidence) ? `Confidence: ${formatConfidence(sourceEvent.event.confidence)}` : ''}
                            </div>
                            {sourceUncertaintyLabel ? <div className="text-[11px] text-amber-200">{sourceUncertaintyLabel}</div> : null}
                          </li>
                          );
                        })}
                      </ul>
                    ) : null}
                  </div>
                  <div className="relative shrink-0" style={{ width: chart.width, height: ROW_HEIGHT }}>
                    {chart.ticks.map((tick) => (
                      <div key={`${item.event.title}-${tick.label}`} className="absolute inset-y-0 w-px bg-slate-800" style={{ left: tick.x }} />
                    ))}
                    {item.isMilestone ? (
                      <div
                        className="absolute h-3 w-3 -translate-x-1/2 rotate-45 rounded-[1px] bg-emerald-400"
                        style={{ left: startX, marginTop: 25 }}
                        data-testid="timeline-milestone"
                      />
                    ) : (
                      <div
                        className="absolute h-3 rounded bg-blue-500"
                        style={{ left: startX, width, marginTop: 25 }}
                        data-testid="timeline-range-bar"
                      />
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
