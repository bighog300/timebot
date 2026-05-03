import { useEffect, useState } from 'react';
import { api, getErrorDetail } from '@/services/api';
import type { EmailProviderConfig } from '@/types/api';

export function AdminEmailSettingsPage(){
  const [items,setItems]=useState<EmailProviderConfig[]>([]); const [err,setErr]=useState('');
  const [keys,setKeys]=useState<Record<string,string>>({});
  useEffect(()=>{api.listEmailProviderConfigs().then(setItems).catch(e=>setErr(getErrorDetail(e)));},[]);
  return <div><h2>Email Providers</h2>{err&&<div>{err}</div>}{items.map(i=><div key={i.provider}><h3>{i.provider}</h3><div>{i.configured?'Configured':'Not configured'}</div><input value={i.from_email} onChange={e=>setItems(v=>v.map(x=>x.provider===i.provider?{...x,from_email:e.target.value}:x))}/><input placeholder='api key' value={keys[i.provider]??''} onChange={e=>setKeys(v=>({...v,[i.provider]:e.target.value}))}/><button onClick={async()=>{const payload: { enabled: boolean; from_email: string; from_name?: string | null; reply_to?: string | null; api_key?: string }={enabled:i.enabled,from_email:i.from_email,from_name:i.from_name,reply_to:i.reply_to}; if((keys[i.provider]??'')!=='') payload.api_key=keys[i.provider]; const updated=await api.patchEmailProviderConfig(i.provider as 'resend'|'sendgrid',payload); setItems(v=>v.map(x=>x.provider===i.provider?updated:x)); setKeys(v=>({...v,[i.provider]:''}));}}>Save</button></div>)}</div>
}
