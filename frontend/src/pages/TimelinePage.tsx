import { useMemo } from 'react';
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

const MS_PER_DAY = 86_400_000;
const LABEL_WIDTH = 320;
const ROW_HEIGHT = 64;
const MIN_CHART_WIDTH = 900;
const PIXELS_PER_DAY = 4;
const MIN_BAR_WIDTH = 6;

export function TimelinePage() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery({ queryKey: ['timeline'], queryFn: api.getTimeline });

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
          isMilestone: Boolean(event.date && !event.end_date),
        };
      })
      .filter((item): item is NormalizedTimelineEvent => Boolean(item));
  }, [data?.events]);

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
    const width = Math.max(MIN_CHART_WIDTH, totalDays * PIXELS_PER_DAY);

    const ticks: Array<{ label: string; x: number }> = [];
    const tickDate = new Date(Date.UTC(paddedMin.getUTCFullYear(), paddedMin.getUTCMonth(), 1));
    while (tickDate <= paddedMax) {
      const x = ((tickDate.getTime() - paddedMin.getTime()) / (paddedMax.getTime() - paddedMin.getTime())) * width;
      ticks.push({ label: tickDate.toLocaleDateString(undefined, { month: 'short', year: 'numeric' }), x });
      tickDate.setUTCMonth(tickDate.getUTCMonth() + 1);
    }

    const dateToX = (date: Date) => ((date.getTime() - paddedMin.getTime()) / (paddedMax.getTime() - paddedMin.getTime())) * width;

    return { width, ticks, dateToX };
  }, [normalizedEvents]);

  if (isLoading) return <div>Loading timeline…</div>;
  if (isError) return <div>Failed to load timeline.</div>;
  if (!normalizedEvents.length) return <div>No extracted timeline events yet. Upload documents with dated events or regenerate intelligence.</div>;
  if (!chart) return null;

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Timeline</h1>
      <div className="overflow-x-auto rounded border border-slate-700" data-testid="timeline-scroll-area">
        <div className="min-w-max" style={{ minWidth: LABEL_WIDTH + chart.width }}>
          <div className="sticky top-0 z-10 flex border-b border-slate-700 bg-slate-900/95">
            <div className="shrink-0 p-3 text-xs font-semibold uppercase tracking-wide text-slate-300" style={{ width: LABEL_WIDTH }}>
              Event / Document
            </div>
            <div className="relative" style={{ width: chart.width, height: 44 }} data-testid="timeline-axis">
              {chart.ticks.map((tick) => (
                <div key={tick.label} className="absolute inset-y-0" style={{ left: tick.x }}>
                  <div className="h-3 w-px bg-slate-500" />
                  <div className="mt-1 -translate-x-1/2 whitespace-nowrap text-xs text-slate-300">{tick.label}</div>
                </div>
              ))}
            </div>
          </div>

          {normalizedEvents.map((item, idx) => {
            const startX = chart.dateToX(item.start);
            const endX = chart.dateToX(item.end);
            const width = Math.max(MIN_BAR_WIDTH, endX - startX);

            return (
              <button
                key={`${item.event.document_id}-${idx}`}
                className="flex w-full border-b border-slate-700 text-left hover:bg-slate-800/60"
                onClick={() => navigate(`/documents/${item.event.document_id}`)}
                title={`${item.event.title} • ${item.event.document_title} • ${item.event.start_date || item.event.date}${item.event.end_date ? ` → ${item.event.end_date}` : ''}${item.event.source_quote ? ` • ${item.event.source_quote}` : ''}`}
              >
                <div className="shrink-0 p-3" style={{ width: LABEL_WIDTH }}>
                  <div className="text-sm font-medium">{item.event.title}</div>
                  <div className="text-xs text-slate-400">{item.event.document_title}</div>
                  <div className="text-xs text-slate-500">confidence: {Math.round(item.event.confidence * 100)}%</div>
                </div>
                <div className="relative" style={{ width: chart.width, height: ROW_HEIGHT }}>
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
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
