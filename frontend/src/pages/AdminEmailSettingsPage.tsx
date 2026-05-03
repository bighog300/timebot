import { useEffect, useState } from 'react';
import { api, getErrorDetail } from '@/services/api';
import type { EmailProviderConfig, EmailProviderConfigPatch, EmailSendLog, EmailTestSendResult } from '@/types/api';

export function AdminEmailSettingsPage() {
  const [items, setItems] = useState<EmailProviderConfig[]>([]);
  const [err, setErr] = useState('');
  const [keys, setKeys] = useState<Record<string, string>>({});
  const [webhookSecrets, setWebhookSecrets] = useState<Record<string, string>>({});
  const [logs, setLogs] = useState<EmailSendLog[]>([]);
  const [toEmail, setToEmail] = useState('');
  const [provider, setProvider] = useState<'default' | 'resend' | 'sendgrid'>('default');
  const [subject, setSubject] = useState('');
  const [htmlBody, setHtmlBody] = useState('');
  const [textBody, setTextBody] = useState('');
  const [result, setResult] = useState<EmailTestSendResult | null>(null);

  useEffect(() => {
    api.listEmailProviderConfigs().then(setItems).catch((e) => setErr(getErrorDetail(e)));
    api.getEmailSendLogs().then(setLogs).catch(() => {});
  }, []);

  return <div>
    <h2>Email Providers</h2>
    {err && <div>{err}</div>}
    {items.map((i) => <div key={i.provider}><h3>{i.provider}</h3><div>{i.configured ? 'Configured' : 'Not configured'} • webhook {i.webhook_configured ? 'Configured' : 'Not configured'}</div><div>/api/v1/email/webhooks/{i.provider}</div><input value={i.from_email} onChange={(e) => setItems((v) => v.map((x) => x.provider === i.provider ? { ...x, from_email: e.target.value } : x))} /><input placeholder='api key' value={keys[i.provider] ?? ''} onChange={(e) => setKeys((v) => ({ ...v, [i.provider]: e.target.value }))} /><input placeholder='webhook secret' value={webhookSecrets[i.provider] ?? ''} onChange={(e)=>setWebhookSecrets((v)=>({...v,[i.provider]:e.target.value}))} /><button onClick={async () => { const payload: EmailProviderConfigPatch = { enabled: i.enabled, from_email: i.from_email, from_name: i.from_name, reply_to: i.reply_to }; if ((keys[i.provider] ?? '') !== '') payload.api_key = keys[i.provider]; if ((webhookSecrets[i.provider] ?? '') !== '') payload.webhook_secret = webhookSecrets[i.provider]; const updated = await api.patchEmailProviderConfig(i.provider as 'resend' | 'sendgrid', payload); setItems((v) => v.map((x) => x.provider === i.provider ? updated : x)); setKeys((v) => ({ ...v, [i.provider]: '' })); setWebhookSecrets((v)=>({...v,[i.provider]:''})); }}>Save</button></div>)}

    <h2>Send test email</h2>
    <select aria-label='provider' value={provider} onChange={(e) => setProvider(e.target.value as 'default' | 'resend' | 'sendgrid')}><option value='default'>default</option><option value='resend'>resend</option><option value='sendgrid'>sendgrid</option></select>
    <input aria-label='to email' value={toEmail} onChange={(e) => setToEmail(e.target.value)} />
    <input aria-label='subject' value={subject} onChange={(e) => setSubject(e.target.value)} />
    <textarea aria-label='html body' value={htmlBody} onChange={(e) => setHtmlBody(e.target.value)} />
    <textarea aria-label='text body' value={textBody} onChange={(e) => setTextBody(e.target.value)} />
    <button onClick={async () => { try { const r = await api.testSendEmail({ provider: provider === 'default' ? undefined : provider, to_email: toEmail, subject: subject || undefined, html_body: htmlBody || undefined, text_body: textBody || undefined }); setResult(r); setErr(''); setLogs(await api.getEmailSendLogs()); } catch (e) { setErr(getErrorDetail(e)); } }}>Send</button>
    {result && <div>status:{result.status} provider:{result.provider} log:{result.log_id}</div>}

    <h2>Recent delivery logs</h2>
    <table><tbody>{logs.map((l) => <tr key={l.id}><td>{l.provider}</td><td>{l.recipient_email}</td><td>{l.subject}</td><td>{l.status}</td><td>{l.provider_message_id ?? ''}</td><td>{l.error_message_sanitized ?? ''}</td><td>{l.sent_at ?? l.failed_at ?? ''}</td></tr>)}</tbody></table>
  </div>;
}
