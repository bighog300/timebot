import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '@/services/api';
import type { EmailTemplate } from '@/types/api';
export function AdminEmailTemplatesPage(){const [items,setItems]=useState<EmailTemplate[]>([]); useEffect(()=>{api.listEmailTemplates().then(setItems);},[]); return <div><h2>Email Templates</h2><Link to='/admin/settings/email/templates/new'>Create template</Link>{items.map(t=><div key={t.id}><Link to={`/admin/settings/email/templates/${t.id}`}>{t.name}</Link> {t.slug} {t.category} {t.status}</div>)}</div>}
