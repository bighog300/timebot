import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api, getErrorDetail } from '@/services/api';
import { Card } from '@/components/ui/Card';
import type { EmailTemplateCreate, EmailTemplatePreviewResponse } from '@/types/api';

const blank: EmailTemplateCreate = { name:'', slug:'', category:'transactional', status:'draft', subject:'', preheader:'', html_body:'', text_body:'', variables_json:{} };

export function AdminEmailTemplateEditorPage(){
  const {templateId}=useParams(); const nav=useNavigate();
  const [f,setF]=useState<EmailTemplateCreate>(blank); const [err,setErr]=useState('');
  const [variablesDraft,setVariablesDraft]=useState('{}'); const [rawMode,setRawMode]=useState(false);
  const [samples,setSamples]=useState<Record<string,string>>({}); const [preview,setPreview]=useState<EmailTemplatePreviewResponse|null>(null);
  const [toEmail,setToEmail]=useState(''); const [sendMsg,setSendMsg]=useState('');
  useEffect(()=>{ if(templateId){ api.getEmailTemplate(templateId).then((t)=>{setF({name:t.name,slug:t.slug,category:t.category,status:t.status,subject:t.subject,preheader:t.preheader ?? '',html_body:t.html_body,text_body:t.text_body ?? '',variables_json:t.variables_json}); setVariablesDraft(JSON.stringify(t.variables_json ?? {}, null, 2));}).catch(e=>setErr(getErrorDetail(e))); } },[templateId]);
  const archived=f.status==='archived';
  const detected = useMemo(()=> Array.from(new Set(`${f.subject}\n${f.preheader ?? ''}\n${f.html_body}\n${f.text_body ?? ''}`.match(/\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}/g)?.map((x)=>x.replace(/[{}\s]/g,'')) ?? [])).sort(), [f]);
  let parsed: Record<string, unknown> | null = null;
  try { parsed = JSON.parse(variablesDraft); } catch { parsed = null; }
  const effective = rawMode ? parsed : { ...(parsed ?? {}), ...samples };
  const canEditArchivedStatusOnly = archived && !!templateId;
  async function refreshPreview(){ if(!effective) return; try{ setPreview(await api.previewEmailTemplate({ subject:f.subject, preheader:f.preheader ?? '', html_body:f.html_body, text_body:f.text_body ?? '', variables_json:effective })); } catch(e){ setErr(getErrorDetail(e)); } }
  useEffect(()=>{ void refreshPreview(); }, [f.subject,f.preheader,f.html_body,f.text_body,variablesDraft,samples,rawMode]);
  return <Card><h2>{templateId?'Edit':'New'} Email Template</h2>{err&&<div>{err}</div>}
  <input value={f.name} disabled={archived} onChange={e=>setF({...f,name:e.target.value})}/>
  <input value={f.slug} disabled={archived} onChange={e=>setF({...f,slug:e.target.value})}/>
  <select value={f.category} disabled={archived} onChange={e=>setF({...f,category:e.target.value as 'transactional'|'campaign'|'system'})}><option value='transactional'>transactional</option><option value='campaign'>campaign</option><option value='system'>system</option></select>
  <select value={f.status} onChange={e=>setF({...f,status:e.target.value as 'draft'|'active'|'archived'})}><option value='draft'>draft</option><option value='active'>active</option><option value='archived'>archived</option></select>
  <input value={f.subject} disabled={archived} onChange={e=>setF({...f,subject:e.target.value})}/>
  <input value={f.preheader ?? ''} disabled={archived} onChange={e=>setF({...f,preheader:e.target.value})}/>
  <textarea value={f.html_body} disabled={archived} onChange={e=>setF({...f,html_body:e.target.value})}/>
  <textarea value={f.text_body ?? ''} disabled={archived} onChange={e=>setF({...f,text_body:e.target.value})}/>
  <h3>Variables helper</h3><label><input type='checkbox' checked={rawMode} onChange={e=>setRawMode(e.target.checked)}/> Raw JSON advanced mode</label>
  <div>Detected: {detected.join(', ') || 'none'}</div><div>Missing: {(preview?.missing_variables ?? []).join(', ') || 'none'}</div>
  {!rawMode && detected.map((k)=><label key={k}>{k}<input value={samples[k] ?? ''} onChange={e=>setSamples({...samples,[k]:e.target.value})}/></label>)}
  <textarea aria-label='variables json' value={variablesDraft} disabled={canEditArchivedStatusOnly} onChange={e=>setVariablesDraft(e.target.value)}/>
  {parsed===null && <div>Variables JSON is invalid.</div>}
  <button disabled={parsed===null} onClick={async()=>{try{ const payload={...f, variables_json: effective ?? {}}; if(templateId){await api.patchEmailTemplate(templateId,payload);} else {const created=await api.createEmailTemplate(payload); nav(`/admin/settings/email/templates/${created.id}`);} }catch(e){setErr(getErrorDetail(e));}}}>Save</button>{templateId&&<button onClick={async()=>{ if(window.confirm('Archive this template?')) await api.archiveEmailTemplate(templateId);}}>Archive</button>}
  {templateId&&<button onClick={async()=>{const t=await api.duplicateEmailTemplate(templateId); nav(`/admin/settings/email/templates/${t.id}`);}}>Duplicate</button>}
  <h3>Rendered preview</h3><div>Subject: {preview?.subject}</div><div>Preheader: {preview?.preheader}</div><div dangerouslySetInnerHTML={{__html: preview?.html_body ?? ''}}/><pre>{preview?.text_body}</pre>
  <h3>Send test email</h3><input placeholder='to@example.com' value={toEmail} onChange={e=>setToEmail(e.target.value)}/><button disabled={!effective} onClick={async()=>{try{const r=await api.testSendEmailTemplate({to_email:toEmail, subject:f.subject, preheader:f.preheader ?? '', html_body:f.html_body, text_body:f.text_body ?? '', variables_json:effective ?? {}}); setSendMsg(`sent via ${r.provider}`);}catch(e){setSendMsg(getErrorDetail(e));}}}>Send test email</button><div>{sendMsg}</div>
  </Card>
}
