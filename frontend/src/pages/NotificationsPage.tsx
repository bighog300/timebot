import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import type { NotificationItem } from '@/types/api';

export function NotificationsPage() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  useEffect(() => { api.listNotifications().then(setItems).catch(() => undefined); }, []);
  return <div><h1 className="mb-3 text-xl font-semibold">Notifications</h1>{items.map((n)=><div key={n.id} className="mb-2 rounded border border-slate-700 p-2">{n.title}</div>)}</div>;
}
