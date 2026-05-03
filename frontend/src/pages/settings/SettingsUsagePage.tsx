import { useUsage } from '@/hooks/useApi';

export function SettingsUsagePage() {
  const usage = useUsage();

  if (usage.isLoading) return <div>Loading usage…</div>;
  if (usage.isError || !usage.data) return <div>Unable to load usage summary.</div>;

  return (
    <section className="space-y-4" aria-label="Usage settings">
      <h2 className="text-xl font-semibold">Personal usage</h2>
      <div className="rounded border border-slate-800 bg-slate-900 p-4 text-sm">
        <div>Current plan: <span className="font-semibold uppercase">{usage.data.plan ?? 'free'}</span></div>
        <div>Documents: {usage.data.documents?.used ?? 0} / {usage.data.documents?.limit ?? '∞'}</div>
        <div>Reports: {usage.data.reports?.used ?? 0} / {usage.data.reports?.limit ?? '∞'}</div>
        <div>Chat messages: {usage.data.chat_messages?.used ?? 0} / {usage.data.chat_messages?.limit ?? '∞'}</div>
      </div>
    </section>
  );
}
