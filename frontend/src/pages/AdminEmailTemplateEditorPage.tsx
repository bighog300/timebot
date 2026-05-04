import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api, getErrorDetail } from '@/services/api';
import { Card } from '@/components/ui/Card';
import type { EmailTemplateCreate, EmailTemplatePreviewResponse } from '@/types/api';

const blank: EmailTemplateCreate = { name:'', slug:'', category:'transactional', status:'draft', subject:'', preheader:'', html_body:'', text_body:'', variables_json:{} };
const VAR_RE = /\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}/g;

function detectVariables(...parts:(string|undefined|null)[]){
  const joined = parts.filter(Boolean).join('\n');
  return Array.from(joined.matchAll(VAR_RE), (m)=>m[1]).filter(Boolean);
}

export function AdminEmailTemplateEditorPage(){
  const {templateId}=useParams(); const nav=useNavigate();
  const [f,setF]=useState<EmailTemplateCreate>(blank); const [err,setErr]=useState('');
  const [variablesDraft,setVariablesDraft]=useState('{}'); const [rawMode,setRawMode]=useState(false);
  const [samples,setSamples]=useState<Record<string,string>>({}); const [preview,setPreview]=useState<EmailTemplatePreviewResponse|null>(null);
  const [toEmail,setToEmail]=useState(''); const [sendMsg,setSendMsg]=useState('');
  useEffect(()=>{ if(templateId){ api.getEmailTemplate(templateId).then((t)=>{setF({name:t.name,slug:t.slug,category:t.category,status:t.status,subject:t.subject,preheader:t.preheader ?? '',html_body:t.html_body,text_body:t.text_body ?? '',variables_json:t.variables_json}); setVariablesDraft(JSON.stringify(t.variables_json ?? {}, null, 2));}).catch(e=>setErr(getErrorDetail(e))); } },[templateId]);
  const archived=f.status==='archived';
  const detected = useMemo(()=> Array.from(new Set(detectVariables(f.subject, f.preheader, f.html_body, f.text_body))).sort(), [f]);
  let parsed: Record<string, unknown> | null = null;
  try { parsed = JSON.parse(variablesDraft); } catch { parsed = null; }
  const effective = rawMode ? parsed : { ...(parsed ?? {}), ...samples };
  const missing = useMemo(() => detected.filter((key)=>!(key in (effective ?? {})) || effective?.[key] === ''), [detected, effective]);
  const canEditArchivedStatusOnly = archived && !!templateId;
  async function refreshPreview(){ if(!effective) return; try{ setPreview(await api.previewEmailTemplate({ subject:f.subject, preheader:f.preheader ?? '', html_body:f.html_body, text_body:f.text_body ?? '', variables_json:effective })); } catch(e){ setErr(getErrorDetail(e)); } }
  useEffect(()=>{ void refreshPreview(); }, [f.subject,f.preheader,f.html_body,f.text_body,variablesDraft,samples,rawMode]);
  return <Card><h2>{templateId?'Edit':'New'} Email Template</h2>{err&&<div>{err}</div>}
  <input aria-label='template name' value={f.name} disabled={archived} onChange={e=>setF({...f,name:e.target.value})}/>
  <input aria-label='template slug' value={f.slug} disabled={archived} onChange={e=>setF({...f,slug:e.target.value})}/>
  <select value={f.category} disabled={archived} onChange={e=>setF({...f,category:e.target.value as 'transactional'|'campaign'|'system'})}><option value='transactional'>transactional</option><option value='campaign'>campaign</option><option value='system'>system</option></select>
  <select value={f.status} onChange={e=>setF({...f,status:e.target.value as 'draft'|'active'|'archived'})}><option value='draft'>draft</option><option value='active'>active</option><option value='archived'>archived</option></select>
  <input aria-label='template subject' value={f.subject} disabled={archived} onChange={e=>setF({...f,subject:e.target.value})}/>
  <input aria-label='template preheader' value={f.preheader ?? ''} disabled={archived} onChange={e=>setF({...f,preheader:e.target.value})}/>
  <textarea aria-label='template html body' value={f.html_body} disabled={archived} onChange={e=>setF({...f,html_body:e.target.value})}/>
  <textarea aria-label='template text body' value={f.text_body ?? ''} disabled={archived} onChange={e=>setF({...f,text_body:e.target.value})}/>
  <h3>Variables helper</h3><label><input type='checkbox' checked={rawMode} onChange={e=>setRawMode(e.target.checked)}/> Raw JSON advanced mode</label>
  <div>Detected variables: {detected.join(', ') || 'none'}</div><div>Missing variables: {missing.join(', ') || 'none'}</div>
  {!rawMode && detected.map((k)=><label key={k}>{k}<input aria-label={`sample ${k}`} value={(effective?.[k] as string) ?? samples[k] ?? ''} onChange={e=>setSamples({...samples,[k]:e.target.value})}/></label>)}
  <textarea aria-label='variables json' value={variablesDraft} disabled={canEditArchivedStatusOnly} onChange={e=>setVariablesDraft(e.target.value)}/>
  {parsed===null && <div>Variables JSON is invalid.</div>}
  <button disabled={parsed===null} onClick={async()=>{try{ const payload={...f, variables_json: effective ?? {}}; if(templateId){await api.patchEmailTemplate(templateId,payload);} else {const created=await api.createEmailTemplate(payload); nav(`/admin/settings/email/templates/${created.id}`);} }catch(e){setErr(getErrorDetail(e));}}}>Save</button>{templateId&&<button onClick={async()=>{ if(window.confirm('Archive this template?')) await api.archiveEmailTemplate(templateId);}}>Archive</button>}
  {templateId&&<button onClick={async()=>{const t=await api.duplicateEmailTemplate(templateId); nav(`/admin/settings/email/templates/${t.id}`);}}>Duplicate template</button>}
  <h3>Rendered preview</h3><div><strong>Subject preview:</strong> {preview?.subject}</div><div><strong>Preheader preview:</strong> {preview?.preheader}</div><div><strong>HTML preview:</strong><div dangerouslySetInnerHTML={{__html: preview?.html_body ?? ''}}/></div><div><strong>Text preview:</strong><pre>{preview?.text_body}</pre></div>
  <h3>Send test email</h3><input placeholder='to@example.com' value={toEmail} onChange={e=>setToEmail(e.target.value)}/><button disabled={!effective} onClick={async()=>{try{const r=await api.testSendEmailTemplate({to_email:toEmail, subject:f.subject, preheader:f.preheader ?? '', html_body:f.html_body, text_body:f.text_body ?? '', variables_json:effective ?? {}}); setSendMsg(`sent via ${r.provider}`);}catch(e){setSendMsg(getErrorDetail(e));}}}>Send test email</button><div>{sendMsg}</div>
  </Card>
}
