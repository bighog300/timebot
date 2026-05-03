import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import type { EmailSuppression } from '@/types/api';

export function AdminEmailSuppressionsPage() {
  const [items, setItems] = useState<EmailSuppression[]>([]);
  const [email, setEmail] = useState('');
  const [reason, setReason] = useState<'manual'|'unsubscribe'|'bounce'|'complaint'>('manual');
  const load = async () => setItems(await api.listEmailSuppressions());
  useEffect(() => { void load(); }, []);
  return <div><h2>Email Suppressions</h2>
    <input aria-label='suppression email' value={email} onChange={e=>setEmail(e.target.value)} />
    <select value={reason} onChange={e=>setReason(e.target.value as typeof reason)}><option value='manual'>manual</option><option value='unsubscribe'>unsubscribe</option><option value='bounce'>bounce</option><option value='complaint'>complaint</option></select>
    <button onClick={async()=>{await api.addEmailSuppression({email,reason}); setEmail(''); await load();}}>Add suppression</button>
    {items.map(i=><div key={i.id}>{i.email} {i.reason} {i.source ?? ''} {i.created_at} <button onClick={async()=>{await api.removeEmailSuppression(i.email); await load();}}>Remove</button></div>)}
  </div>;
}
