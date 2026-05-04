import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/services/api';

export function DivorceSetupPage() {
  const navigate = useNavigate();
  const [caseTitle, setCaseTitle] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');

  return <div className='space-y-3'>
    <h1 className='text-xl font-semibold'>Divorce Setup</h1>
    <p className='text-sm text-slate-300'>Privacy & security: documents and case data stay scoped to your workspace and account access controls.</p>
    <input value={caseTitle} onChange={(e)=>setCaseTitle(e.target.value)} placeholder='Case title' />
    <input value={jurisdiction} onChange={(e)=>setJurisdiction(e.target.value)} placeholder='Jurisdiction' />
    <button onClick={async ()=>{const ws=await api.createDivorceWorkspace({case_title: caseTitle, jurisdiction, current_stage:'considering divorce', children_involved:false, financial_disclosure_started:false, lawyer_involved:false}); localStorage.setItem('active_workspace_id', ws.id); navigate('/divorce');}}>Create</button>
    <p className='text-xs text-slate-400'>Legal disclaimer: This product provides informational support and is not a substitute for a qualified attorney. AI output must be independently verified before legal use.</p>
  </div>;
}
