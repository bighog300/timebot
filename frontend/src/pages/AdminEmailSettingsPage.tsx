import { useEffect, useMemo, useState } from 'react';
import { api, getErrorDetail } from '@/services/api';
import { Card } from '@/components/ui/Card';
import type { EmailProviderConfig, EmailProviderConfigPatch, EmailSendLog, EmailTestSendResult } from '@/types/api';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function AdminEmailSettingsPage() {
  const [items, setItems] = useState<EmailProviderConfig[]>([]);
  const [err, setErr] = useState('');
  const [status, setStatus] = useState('');
  const [savingProvider, setSavingProvider] = useState<string | null>(null);
  const [keys, setKeys] = useState<Record<string, string>>({});
  const [webhookSecrets, setWebhookSecrets] = useState<Record<string, string>>({});
  const [logs, setLogs] = useState<EmailSendLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [toEmail, setToEmail] = useState('');
  const [provider, setProvider] = useState<'default' | 'resend' | 'sendgrid'>('default');
  const [subject, setSubject] = useState('');
  const [htmlBody, setHtmlBody] = useState('');
  const [textBody, setTextBody] = useState('');
  const [result, setResult] = useState<EmailTestSendResult | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [providerRows, logRows] = await Promise.all([api.listEmailProviderConfigs(), api.getEmailSendLogs()]);
      setItems(providerRows);
      setLogs(logRows);
      setErr('');
    } catch (e) {
      setErr(getErrorDetail(e));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { void load(); }, []);

  const webhookBase = useMemo(() => `${window.location.origin}/api/v1/email/webhooks`, []);

  async function saveProvider(i: EmailProviderConfig, clearWebhookSecret = false) {
    if (i.from_email && !EMAIL_RE.test(i.from_email)) return setErr(`Invalid from email for ${i.provider}`);
    if (i.reply_to && !EMAIL_RE.test(i.reply_to)) return setErr(`Invalid reply-to email for ${i.provider}`);
    setSavingProvider(i.provider);
    setStatus('');
    try {
      const payload: EmailProviderConfigPatch = { enabled: i.enabled, from_email: i.from_email, from_name: i.from_name, reply_to: i.reply_to, clear_webhook_secret: clearWebhookSecret || undefined };
      if ((keys[i.provider] ?? '').trim() !== '') payload.api_key = keys[i.provider].trim();
      if ((webhookSecrets[i.provider] ?? '').trim() !== '') payload.webhook_secret = webhookSecrets[i.provider].trim();
      const updated = await api.patchEmailProviderConfig(i.provider as 'resend' | 'sendgrid', payload);
      setItems((v) => v.map((x) => x.provider === i.provider ? updated : x));
      setKeys((v) => ({ ...v, [i.provider]: '' }));
      setWebhookSecrets((v)=>({...v,[i.provider]:''}));
      setStatus(`${i.provider} saved.`);
      setErr('');
    } catch (e) {
      setErr(getErrorDetail(e));
    } finally {
      setSavingProvider(null);
    }
  }

  return <div className='space-y-4'>
    <h2 className='text-lg font-semibold'>Email Providers</h2>
    {loading && <Card><div>Loading email settings...</div></Card>}
    {err && <Card><div className='text-rose-300'>{err}</div></Card>}
    {status && <Card><div className='text-emerald-300'>{status}</div></Card>}
    {!loading && items.map((i) => <Card key={i.provider}>
      <h3 className='text-base font-semibold'>{i.provider}</h3>
      <p className='text-sm text-slate-300'>{i.configured ? 'API key configured' : 'API key not configured'} · {i.webhook_configured ? 'Webhook secret configured' : 'Webhook secret not configured'} · {i.provider==='resend' ? 'Resend API keys usually start with re_ and your From email must be a verified domain in Resend.' : 'SendGrid API keys usually start with SG. and sender identity must be verified in SendGrid.'}</p>
      <p className='text-xs text-slate-400'>Webhook endpoint: {webhookBase}/{i.provider}. {i.provider==='resend' ? 'Resend → Webhooks: add this URL, subscribe to delivered/opened/clicked/bounced/complained events, then paste the webhook signing secret here.' : 'SendGrid → Settings → Mail Settings → Event Webhook: enable signed event webhook, add this URL, then paste the verification key here as webhook secret.'}</p>
      <div className='mt-3 grid gap-2 md:grid-cols-2'>
        <label>Enabled <input type='checkbox' checked={i.enabled} onChange={(e) => setItems((v) => v.map((x) => x.provider === i.provider ? { ...x, enabled: e.target.checked } : x))} /></label>
        <label>From email <input value={i.from_email} onChange={(e) => setItems((v) => v.map((x) => x.provider === i.provider ? { ...x, from_email: e.target.value } : x))} /></label>
        <label>From name <input value={i.from_name ?? ''} onChange={(e) => setItems((v) => v.map((x) => x.provider === i.provider ? { ...x, from_name: e.target.value || null } : x))} /></label>
        <label>Reply-to <input value={i.reply_to ?? ''} onChange={(e) => setItems((v) => v.map((x) => x.provider === i.provider ? { ...x, reply_to: e.target.value || null } : x))} /></label>
        <label>Replace API key <input type='password' placeholder='Enter new key' value={keys[i.provider] ?? ''} onChange={(e) => setKeys((v) => ({ ...v, [i.provider]: e.target.value }))} /></label>
        <label>Replace webhook secret <input type='password' placeholder='Enter new webhook secret' value={webhookSecrets[i.provider] ?? ''} onChange={(e)=>setWebhookSecrets((v)=>({...v,[i.provider]:e.target.value}))} /></label>
      </div>
      <div className='mt-3 flex gap-2'>
        <button disabled={savingProvider===i.provider} onClick={() => void saveProvider(i)}>Save provider</button>
        <button disabled={savingProvider===i.provider} onClick={() => void saveProvider(i, true)}>Clear webhook secret</button>
      </div>
    </Card>)}

    <Card>
      <h3 className='text-base font-semibold'>Send test email</h3>
      <div className='grid gap-2 md:grid-cols-2'>
        <select aria-label='provider' value={provider} onChange={(e) => setProvider(e.target.value as 'default' | 'resend' | 'sendgrid')}><option value='default'>default</option><option value='resend'>resend</option><option value='sendgrid'>sendgrid</option></select>
        <input aria-label='to email' value={toEmail} onChange={(e) => setToEmail(e.target.value)} placeholder='to@example.com' />
        <input aria-label='subject' value={subject} onChange={(e) => setSubject(e.target.value)} placeholder='Subject (optional)' />
      </div>
      <textarea aria-label='html body' value={htmlBody} onChange={(e) => setHtmlBody(e.target.value)} placeholder='HTML body (optional)' />
      <textarea aria-label='text body' value={textBody} onChange={(e) => setTextBody(e.target.value)} placeholder='Text body (optional)' />
      <button onClick={async () => { try { const r = await api.testSendEmail({ provider: provider === 'default' ? undefined : provider, to_email: toEmail, subject: subject || undefined, html_body: htmlBody || undefined, text_body: textBody || undefined }); setResult(r); setErr(''); setLogs(await api.getEmailSendLogs()); } catch (e) { setErr(getErrorDetail(e)); } }}>Send</button>
      {result && <div>status:{result.status} provider:{result.provider} log:{result.log_id}</div>}
    </Card>

    <Card>
      <h3 className='text-base font-semibold'>Recent send logs</h3>
      {logs.length===0 ? <div className='text-sm text-slate-400'>No send logs yet.</div> : <table><thead><tr><th>Status</th><th>Provider</th><th>Recipient</th><th>Subject</th><th>Provider Message ID</th><th>Error</th><th>Timestamp</th></tr></thead><tbody>{logs.map((l) => <tr key={l.id}><td>{l.status}</td><td>{l.provider}</td><td>{l.recipient_email}</td><td>{l.subject}</td><td>{l.provider_message_id ?? ''}</td><td>{l.error_message_sanitized ?? ''}</td><td>{l.sent_at ?? l.failed_at ?? l.created_at ?? ''}</td></tr>)}</tbody></table>}
    </Card>
  </div>;
}
