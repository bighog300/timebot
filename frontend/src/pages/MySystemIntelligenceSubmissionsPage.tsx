import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { useMySystemIntelligenceSubmissions, useWithdrawSystemIntelligenceSubmission } from '@/hooks/useApi';

export function MySystemIntelligenceSubmissionsPage() {
  const q = useMySystemIntelligenceSubmissions();
  const withdraw = useWithdrawSystemIntelligenceSubmission();

  return <div className='space-y-3'>
    <h1 className='text-xl font-semibold'>My System Intelligence Submissions</h1>
    {(q.data || []).map((s) => <Card key={s.id}><div className='space-y-1 text-sm'>
      <div className='font-medium'>{s.source_document_title || s.source_document_id} ({s.status})</div>
      <div>Suggested: {s.suggested_category || '-'} / {s.suggested_jurisdiction || '-'}</div>
      <div>Reason: {s.reason}</div>
      {s.admin_notes && <div>Admin notes: {s.admin_notes}</div>}
      <div>Reviewed at: {s.reviewed_at || '-'}</div>
      {s.resulting_system_document_id && <div>Resulting system document: {s.resulting_system_document_id}</div>}
      {s.status === 'pending' && <Button onClick={() => withdraw.mutate(s.id)}>Withdraw</Button>}
    </div></Card>)}
  </div>;
}
