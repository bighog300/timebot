import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api } from '@/services/api';

const CHECKLIST = [
  'Complete setup',
  'Upload documents',
  'Extract tasks',
  'Build timeline',
  'Generate first report',
  'Ask an advisor',
] as const;

export function DivorceDashboardPage() {
  const navigate = useNavigate();
  const workspaceId = localStorage.getItem('active_workspace_id') || '';
  const { data } = useQuery({ queryKey: ['divorce-dash', workspaceId], queryFn: () => api.getDivorceDashboard(workspaceId), enabled: !!workspaceId });
  const advisors = useQuery({ queryKey: ['divorce-advisors'], queryFn: () => api.getDivorceAdvisors() });
  const createChat = useMutation({ mutationFn: api.createChatSession, onSuccess: () => navigate('/chat') });

  const launchAdvisor = async (key: string) => {
    const mapped = advisors.data?.find((a) => a.key === key);
    if (!mapped) return;
    if (mapped.locked) {
      navigate('/upgrade');
      return;
    }
    await createChat.mutateAsync({ title: mapped.chat_title, assistant_id: mapped.assistant_id, prompt_template_id: mapped.prompt_template_id });
  };

  const done = {
    'Complete setup': Boolean(workspaceId),
    'Upload documents': (data?.documents_uploaded || 0) > 0,
    'Extract tasks': (data?.suggested_task_count || 0) + (data?.open_task_count || 0) > 0,
    'Build timeline': (data?.suggested_timeline_count || 0) + (data?.accepted_timeline_count || 0) > 0,
    'Generate first report': (data?.report_count || 0) > 0,
    'Ask an advisor': false,
  } as Record<(typeof CHECKLIST)[number], boolean>;

  const cards = [
    { label: 'Ask Legal Advisor', action: () => launchAdvisor('legal_advisor') },
    { label: 'Ask Psychology Advisor', action: () => launchAdvisor('psychology_advisor') },
    { label: 'Analyze Documents', action: () => launchAdvisor('document_analyst') },
    { label: 'Build Timeline', action: () => navigate('/divorce/timeline') },
    { label: 'Generate Lawyer Pack', action: () => navigate('/divorce/reports') },
    { label: 'Review Tasks', action: () => navigate('/divorce/tasks') },
  ];

  return <div className='space-y-4'>
    <h1 className='text-xl font-semibold'>Divorce Dashboard</h1>
    <section>
      <h2 className='font-medium'>Guided checklist</h2>
      <ul>{CHECKLIST.map((item) => <li key={item}>{done[item] ? '✅' : '⬜'} {item}</li>)}</ul>
    </section>
    <section className='grid gap-2 md:grid-cols-2'>
      {cards.map((card) => {
        const mapped = advisors.data?.find((a) => card.label.includes('Legal') ? a.key === 'legal_advisor' : card.label.includes('Psychology') ? a.key === 'psychology_advisor' : card.label.includes('Analyze') ? a.key === 'document_analyst' : false);
        return <button key={card.label} className='rounded border p-3 text-left' onClick={card.action}>
          <div className='font-medium'>{card.label}</div>
          {mapped?.locked ? <div className='text-amber-400'>🔒 Pro · Upgrade to unlock</div> : null}
          <div className='text-xs text-slate-400'>Launch</div>
        </button>;
      })}
    </section>
  </div>;
}
