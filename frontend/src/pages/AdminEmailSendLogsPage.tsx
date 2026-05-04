import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/Card';
import { api, getErrorDetail } from '@/services/api';
import type { EmailSendLog } from '@/types/api';

export function AdminEmailSendLogsPage() {
  const [rows, setRows] = useState<EmailSendLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        setRows(await api.getEmailSendLogs());
        setError('');
      } catch (e) {
        setError(getErrorDetail(e));
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, []);

  return <div className='space-y-4'>
    <h2 className='text-lg font-semibold'>Email Send Logs</h2>
    {loading && <Card><div className='text-sm text-slate-300'>Loading send logs…</div></Card>}
    {!loading && error && <Card><div className='text-sm text-rose-300'>{error}</div></Card>}
    {!loading && !error && rows.length === 0 && <Card><div className='text-sm text-slate-400'>No send logs yet.</div></Card>}
    {!loading && !error && rows.length > 0 && <Card>
      <div className='overflow-auto'>
        <table className='min-w-full text-sm'>
          <thead>
            <tr>
              <th>Provider</th><th>Recipient</th><th>Subject</th><th>Status</th><th>Provider Message ID</th><th>Error</th><th>Created</th><th>Sent</th><th>Failed</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((l)=><tr key={l.id}>
              <td>{l.provider}</td><td>{l.recipient_email}</td><td>{l.subject}</td><td>{l.status}</td><td>{l.provider_message_id ?? '—'}</td><td>{l.error_message_sanitized ?? '—'}</td><td>{l.created_at ?? '—'}</td><td>{l.sent_at ?? '—'}</td><td>{l.failed_at ?? '—'}</td>
            </tr>)}
          </tbody>
        </table>
      </div>
    </Card>}
  </div>;
}
