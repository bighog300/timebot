import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api, getErrorDetail } from '@/services/api';
import type { EmailTemplateCreate } from '@/types/api';

const blank: EmailTemplateCreate = { name:'', slug:'', category:'transactional', status:'draft', subject:'', preheader:'', html_body:'', text_body:'', variables_json:{} };

export function AdminEmailTemplateEditorPage(){
  const {templateId}=useParams(); const nav=useNavigate(); const [f,setF]=useState<EmailTemplateCreate>(blank); const [err,setErr]=useState('');
  useEffect(()=>{ if(templateId){ api.getEmailTemplate(templateId).then((t)=>setF({name:t.name,slug:t.slug,category:t.category,status:t.status,subject:t.subject,preheader:t.preheader ?? '',html_body:t.html_body,text_body:t.text_body ?? '',variables_json:t.variables_json})).catch(e=>setErr(getErrorDetail(e))); } },[templateId]);
  const archived=f.status==='archived';
  return <div><h2>{templateId?'Edit':'New'} Email Template</h2>{err&&<div>{err}</div>}<input value={f.name} disabled={archived} onChange={e=>setF({...f,name:e.target.value})}/><input value={f.slug} disabled={archived} onChange={e=>setF({...f,slug:e.target.value})}/><textarea value={f.html_body} disabled={archived} onChange={e=>setF({...f,html_body:e.target.value})}/><textarea value={JSON.stringify(f.variables_json)} disabled={archived} onChange={e=>setF({...f,variables_json:JSON.parse(e.target.value||'{}')})}/><button onClick={async()=>{try{ if(templateId){await api.patchEmailTemplate(templateId,f);} else {const created=await api.createEmailTemplate(f); nav(`/admin/settings/email/templates/${created.id}`);} }catch(e){setErr(getErrorDetail(e));}}}>Save</button>{templateId&&<button onClick={async()=>{await api.archiveEmailTemplate(templateId);}}>Archive</button>}</div>
}
