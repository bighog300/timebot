import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { DivorceDashboardPage } from './DivorceDashboardPage';

const nav = vi.hoisted(()=>vi.fn());
const mocks = vi.hoisted(()=>({create:vi.fn().mockResolvedValue({id:'s1'}), getDashboard: vi.fn().mockResolvedValue({documents_uploaded:1,suggested_task_count:1,open_task_count:0,suggested_timeline_count:0,accepted_timeline_count:0,report_count:0})}));
vi.mock('react-router-dom', async (orig)=>({...(await orig() as object), useNavigate:()=>nav}));
vi.mock('@/services/api', ()=>({api:{
  getDivorceDashboard: mocks.getDashboard,
  getDivorceAdvisors: vi.fn().mockResolvedValue([
    {key:'legal_advisor',label:'Ask Legal Advisor',assistant_id:'a1',prompt_template_id:'t1',locked:false,chat_title:'Legal advisor session'},
    {key:'psychology_advisor',label:'Ask Psychology Advisor',assistant_id:'a2',prompt_template_id:'t2',locked:true,chat_title:'Psychology advisor session'},
    {key:'document_analyst',label:'Analyze Documents',assistant_id:'a3',prompt_template_id:'t3',locked:false,chat_title:'Document analysis session'},
  ]),
  createChatSession: mocks.create,
}}));

describe('DivorceDashboardPage', ()=>{
  it('renders launcher cards and routes feature cards', async ()=>{
    localStorage.setItem('activeWorkspaceId','ws1');
    render(<MemoryRouter><QueryClientProvider client={new QueryClient()}><DivorceDashboardPage/></QueryClientProvider></MemoryRouter>);
    expect(await screen.findByText('Ask Legal Advisor')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Build Timeline'));
    expect(nav).toHaveBeenCalledWith('/divorce/timeline');
    fireEvent.click(screen.getByRole('button', { name: /Upload documents/i }));
    expect(nav).toHaveBeenCalledWith('/documents');
    fireEvent.click(screen.getByRole('button', { name: /Generate first report/i }));
    expect(nav).toHaveBeenCalledWith('/divorce/reports');
    expect(mocks.getDashboard).toHaveBeenCalledWith('ws1');
  });

  it('creates legal advisor chat with mapping', async ()=>{
    localStorage.setItem('activeWorkspaceId','ws1');
    render(<MemoryRouter><QueryClientProvider client={new QueryClient()}><DivorceDashboardPage/></QueryClientProvider></MemoryRouter>);
    fireEvent.click(await screen.findByText('Ask Legal Advisor'));
    await waitFor(()=>expect(mocks.create).toHaveBeenCalledWith(expect.objectContaining({assistant_id:'a1',prompt_template_id:'t1'})));
  });

  it('locked advisor routes to upgrade', async ()=>{
    localStorage.setItem('activeWorkspaceId','ws1');
    render(<MemoryRouter><QueryClientProvider client={new QueryClient()}><DivorceDashboardPage/></QueryClientProvider></MemoryRouter>);
    fireEvent.click(await screen.findByText('Ask Psychology Advisor'));
    await waitFor(()=>expect(nav).toHaveBeenCalledWith('/upgrade'));
  });
});
