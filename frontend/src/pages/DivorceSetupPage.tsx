import { useState } from 'react';
import { api } from '@/services/api';

export function DivorceSetupPage() {
  const [caseTitle, setCaseTitle] = useState('');
  const [jurisdiction, setJurisdiction] = useState('');
  return <div><h1>Divorce Setup</h1><input value={caseTitle} onChange={(e)=>setCaseTitle(e.target.value)} placeholder='Case title' /><input value={jurisdiction} onChange={(e)=>setJurisdiction(e.target.value)} placeholder='Jurisdiction' /><button onClick={async ()=>{const ws=await api.createDivorceWorkspace({case_title: caseTitle, jurisdiction, current_stage:'considering divorce', children_involved:false, financial_disclosure_started:false, lawyer_involved:false}); localStorage.setItem('active_workspace_id', ws.id);}}>Create</button><p>This is not a substitute for a qualified attorney. AI output must be verified.</p></div>;
}
