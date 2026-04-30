import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/services/api';
import type { TimelineEvent } from '@/types/api';

export function TimelinePage() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQuery({ queryKey: ['timeline'], queryFn: api.getTimeline });

  const events = data?.events ?? [];
  const dated = useMemo(() => events.filter((e) => e.date || e.start_date), [events]);
  if (isLoading) return <div>Loading timeline…</div>;
  if (isError) return <div>Failed to load timeline.</div>;
  if (!dated.length) return <div>No extracted timeline events yet. Upload documents with dated events or regenerate intelligence.</div>;

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Timeline</h1>
      <div className="overflow-x-auto">
        <div className="min-w-[900px]">
          {dated.map((event, idx) => (
            <TimelineRow key={`${event.document_id}-${idx}`} event={event} onClick={() => navigate(`/documents/${event.document_id}`)} />
          ))}
        </div>
      </div>
    </div>
  );
}

function TimelineRow({ event, onClick }: { event: TimelineEvent; onClick: () => void }) {
  const isRange = Boolean(event.start_date && event.end_date);
  return (
    <button className="w-full border-b border-slate-700 py-2 text-left" onClick={onClick}>
      <div className="text-sm font-medium">{event.title} <span className="text-xs text-slate-400">({event.document_title})</span></div>
      <div className="text-xs text-slate-400">confidence: {Math.round(event.confidence * 100)}%</div>
      <div className="mt-1 h-5">
        {isRange ? <div className="h-2 w-64 rounded bg-blue-500" /> : <div className="h-3 w-3 rounded-full bg-emerald-400" />}
      </div>
      <div className="text-xs">{isRange ? `${event.start_date} → ${event.end_date}` : event.date}</div>
      {event.source === 'upload_date' && <div className="text-xs text-amber-300">Upload date fallback</div>}
      {event.source_quote && <div className="text-xs text-slate-300">“{event.source_quote}”</div>}
    </button>
  );
}
