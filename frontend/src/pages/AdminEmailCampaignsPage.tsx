import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, getErrorDetail } from '@/services/api';
import type { EmailCampaign } from '@/types/api';

export function AdminEmailCampaignsPage(){
  const [items,setItems]=useState<EmailCampaign[]>([]); const [err,setErr]=useState(''); const [loading,setLoading]=useState(true);
  useEffect(()=>{api.listEmailCampaigns().then(setItems).catch(e=>setErr(getErrorDetail(e))).finally(()=>setLoading(false));},[]);
  return <div><h2>Email Campaigns</h2><Link to='/admin/settings/email/campaigns/new'>Create campaign</Link>{loading?'Loading...':err?err:items.length===0?'No campaigns yet':items.map(c=><div key={c.id}><Link to={`/admin/settings/email/campaigns/${c.id}`}>{c.name}</Link> {c.audience_type} {c.status} {c.updated_at}</div>)}</div>;
}
