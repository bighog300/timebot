import { useEffect, useMemo, useState } from 'react';
import { api, getErrorDetail } from '@/services/api';
import type { NotificationItem } from '@/types/api';

export function NotificationsPage() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try { setItems(await api.listNotifications()); } catch (e) { setError(getErrorDetail(e)); } finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, []);
  const unread = useMemo(() => items.filter((n) => !n.read_at).length, [items]);

  return <div className='space-y-3'>
    <div className='flex items-center justify-between'>
      <h1 className='text-xl font-semibold'>Notifications</h1>
      <button disabled={!unread} className='rounded border border-slate-700 px-3 py-1 text-sm disabled:opacity-50' onClick={async ()=>{ await api.markAllNotificationsRead(); await load(); }}>Mark all read</button>
    </div>
    {loading ? <div className='text-sm text-slate-400'>Loading notifications...</div> : null}
    {error ? <div className='rounded border border-red-600 bg-red-950/20 p-2 text-sm'>{error}</div> : null}
    {!loading && !items.length ? <div className='text-sm text-slate-400'>No notifications yet.</div> : null}
    {items.map((n)=><div key={n.id} className={`rounded border p-3 ${n.read_at ? 'border-slate-700' : 'border-blue-600 bg-blue-950/20'}`}>
      <div className='flex items-start justify-between gap-2'>
        <div><div className='font-medium'>{n.title}</div><div className='text-sm text-slate-300'>{n.body}</div></div>
        {!n.read_at ? <button className='rounded border border-slate-700 px-2 py-1 text-xs' onClick={async ()=>{ await api.markNotificationRead(n.id); await load(); }}>Mark read</button> : <span className='text-xs text-slate-400'>Read</span>}
      </div>
    </div>)}
  </div>;
}
