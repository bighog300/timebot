import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, getErrorDetail } from '@/services/api';
import { Card } from '@/components/ui/Card';
import type { EmailTemplate } from '@/types/api';
export function AdminEmailTemplatesPage(){const [items,setItems]=useState<EmailTemplate[]>([]); const [loading,setLoading]=useState(true); const [err,setErr]=useState(''); useEffect(()=>{api.listEmailTemplates().then(setItems).catch((e)=>setErr(getErrorDetail(e))).finally(()=>setLoading(false));},[]); return <Card><h2>Email Templates</h2><Link to='/admin/settings/email/templates/new'>Create template</Link>{loading?'Loading templates...':err?err:items.length===0?'No templates yet.':<table><tbody>{items.map(t=><tr key={t.id}><td><Link to={`/admin/settings/email/templates/${t.id}`}>{t.name}</Link></td><td>{t.slug}</td><td>{t.category}</td><td>{t.status}</td></tr>)}</tbody></table>}</Card>}
