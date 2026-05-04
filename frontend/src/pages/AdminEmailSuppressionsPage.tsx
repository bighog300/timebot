import { useEffect, useState } from 'react';
import { api, getErrorDetail } from '@/services/api';
import { Card } from '@/components/ui/Card';
import type { EmailSuppression } from '@/types/api';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function AdminEmailSuppressionsPage() {
  const [items, setItems] = useState<EmailSuppression[]>([]);
  const [email, setEmail] = useState('');
  const [reason, setReason] = useState<'manual'|'unsubscribe'|'bounce'|'complaint'>('manual');
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const load = async () => { setLoading(true); try { setItems(await api.listEmailSuppressions()); setErr(''); } catch (e) { setErr(getErrorDetail(e)); } finally { setLoading(false); } };
  useEffect(() => { void load(); }, []);
  return <Card><h2>Email Suppressions</h2>
    {loading ? <div>Loading suppressions...</div> : err ? <div>{err}</div> : null}
    <input aria-label='suppression email' value={email} onChange={e=>setEmail(e.target.value)} />
    <select value={reason} onChange={e=>setReason(e.target.value as typeof reason)}><option value='manual'>manual</option><option value='unsubscribe'>unsubscribe</option><option value='bounce'>bounce</option><option value='complaint'>complaint</option></select>
    <button onClick={async()=>{ if(!EMAIL_RE.test(email.trim())) return setErr('Invalid email address.'); await api.addEmailSuppression({email,reason}); setEmail(''); await load();}}>Add suppression</button>
    {!loading && !err && items.length===0 && <div>No suppressions yet.</div>}
    {items.map(i=><div key={i.id}>{i.email} {i.reason} {i.source ?? ''} {i.created_at} <button onClick={async()=>{ if(!window.confirm(`Remove suppression for ${i.email}?`)) return; await api.removeEmailSuppression(i.email); await load();}}>Remove</button></div>)}
  </Card>;
}
