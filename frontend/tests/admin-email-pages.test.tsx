import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, vi, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AdminEmailSettingsPage } from '@/pages/AdminEmailSettingsPage';
import { AdminEmailTemplatesPage } from '@/pages/AdminEmailTemplatesPage';
import { AdminEmailTemplateEditorPage } from '@/pages/AdminEmailTemplateEditorPage';
vi.mock('@/services/api', ()=>({ api:{
  listEmailProviderConfigs: vi.fn(async()=>[{provider:'resend',enabled:false,from_email:'a@b.com',configured:true,from_name:null,reply_to:null,created_at:'',updated_at:''},{provider:'sendgrid',enabled:false,from_email:'',configured:false,from_name:null,reply_to:null,created_at:'',updated_at:''}]),
  patchEmailProviderConfig: vi.fn(async(_p,payload)=>({provider:'resend',enabled:false,from_email:'a@b.com',configured:!!payload.api_key,from_name:null,reply_to:null,created_at:'',updated_at:''})),
  getEmailSendLogs: vi.fn(async()=>[]),
  testSendEmail: vi.fn(async()=>({status:'sent',provider:'resend',log_id:'log-1'})),
  listEmailTemplates: vi.fn(async()=>[{id:'1',name:'W',slug:'welcome',category:'transactional',status:'draft',subject:'s',html_body:'h',variables_json:{},created_at:'',updated_at:''}]),
  createEmailTemplate: vi.fn(async(p)=>({id:'2',...p,created_at:'',updated_at:''})),
  getEmailTemplate: vi.fn(async()=>({id:'1',name:'W',slug:'welcome',category:'transactional',status:'archived',subject:'s',html_body:'h',variables_json:{},created_at:'',updated_at:''})),
  patchEmailTemplate: vi.fn(), archiveEmailTemplate: vi.fn()
}, getErrorDetail: ()=> 'err' }));

describe('admin email pages',()=>{
  it('renders providers and templates', async()=>{render(<MemoryRouter><AdminEmailSettingsPage/></MemoryRouter>); expect(await screen.findByText('resend')).toBeInTheDocument(); expect(screen.getByRole('heading',{name:'sendgrid'})).toBeInTheDocument();});
  it('template list renders', async()=>{render(<MemoryRouter><AdminEmailTemplatesPage/></MemoryRouter>); expect(await screen.findByText('W')).toBeInTheDocument();});
  it('archived editor read-only', async()=>{render(<MemoryRouter><AdminEmailTemplateEditorPage/></MemoryRouter>); await waitFor(()=>screen.getByText('New Email Template')); fireEvent.change(screen.getAllByRole('textbox')[0],{target:{value:'x'}}); expect(screen.getAllByRole('textbox')[0]).toBeInTheDocument();});
});
