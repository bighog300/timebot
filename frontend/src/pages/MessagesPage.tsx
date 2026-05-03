import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import type { MessageThread } from '@/types/api';

export function MessagesPage() {
  const [threads, setThreads] = useState<MessageThread[]>([]);
  useEffect(() => { api.listMessages().then(setThreads).catch(() => undefined); }, []);
  return <div><h1 className="mb-3 text-xl font-semibold">Messages</h1>{threads.map((t)=><div key={t.id} className="mb-2 rounded border border-slate-700 p-2">{t.subject} ({t.status})</div>)}</div>;
}
