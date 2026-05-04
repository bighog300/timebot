import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, vi, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AdminEmailSettingsPage } from '@/pages/AdminEmailSettingsPage';
import { AdminEmailTemplatesPage } from '@/pages/AdminEmailTemplatesPage';
import { AdminEmailTemplateEditorPage } from '@/pages/AdminEmailTemplateEditorPage';

const apiMock = {
  listEmailProviderConfigs: vi.fn(async()=>[{provider:'resend',enabled:false,from_email:'a@b.com',configured:true,webhook_configured:true,from_name:null,reply_to:null,created_at:'',updated_at:''},{provider:'sendgrid',enabled:false,from_email:'',configured:false,webhook_configured:false,from_name:null,reply_to:null,created_at:'',updated_at:''}]),
  patchEmailProviderConfig: vi.fn(async(_p,payload)=>({provider:'resend',enabled:false,from_email:'a@b.com',configured:!!payload.api_key,webhook_configured:false,from_name:null,reply_to:null,created_at:'',updated_at:''})),
  getEmailSendLogs: vi.fn(async()=>[]),
  testSendEmail: vi.fn(async()=>({status:'sent',provider:'resend',log_id:'log-1'})),
  listEmailTemplates: vi.fn(async()=>[{id:'1',name:'W',slug:'welcome',category:'transactional',status:'draft',subject:'s',html_body:'h',variables_json:{},created_at:'',updated_at:''}]),
  createEmailTemplate: vi.fn(async(p)=>({id:'2',...p,created_at:'',updated_at:''})),
  getEmailTemplate: vi.fn(async()=>({id:'1',name:'W',slug:'welcome',category:'transactional',status:'archived',subject:'Hi {{name}}',preheader:'For {{team}}',html_body:'<p>{{name}}</p>',text_body:'{{team}}',variables_json:{name:'Ada'},created_at:'',updated_at:''})),
  previewEmailTemplate: vi.fn(async(payload)=>({subject:payload.subject.replace('{{name}}','Ada'),preheader:payload.preheader.replace('{{team}}','Ops'),html_body:'<p>Ada</p>',text_body:'Ops',detected_variables:['name','team'],missing_variables:[]})),
  testSendEmailTemplate: vi.fn(async()=>({status:'sent',provider:'resend',log_id:'1'})),
  duplicateEmailTemplate: vi.fn(async()=>({id:'2'})),
  patchEmailTemplate: vi.fn(), archiveEmailTemplate: vi.fn()
};
vi.mock('@/services/api', ()=>({ api: apiMock, getErrorDetail: ()=> 'err' }));

describe('admin email pages',()=>{
  it('renders providers and templates', async()=>{render(<MemoryRouter><AdminEmailSettingsPage/></MemoryRouter>); expect(await screen.findByText('resend')).toBeInTheDocument(); expect(screen.getByRole('heading',{name:'sendgrid'})).toBeInTheDocument();});
  it('template list renders', async()=>{render(<MemoryRouter><AdminEmailTemplatesPage/></MemoryRouter>); expect(await screen.findByText('W')).toBeInTheDocument();});
  it('editor preview + variables + test send', async()=>{
    render(<MemoryRouter><AdminEmailTemplateEditorPage/></MemoryRouter>);
    await waitFor(()=>screen.getByText('New Email Template'));
    fireEvent.change(screen.getByLabelText('template subject'), { target: { value: 'Hi {{first_name}}' } });
    fireEvent.change(screen.getByLabelText('template preheader'), { target: { value: 'Team {{team}}' } });
    fireEvent.change(screen.getByLabelText('template html body'), { target: { value: '<p>{{first_name}}</p>' } });
    fireEvent.change(screen.getByLabelText('template text body'), { target: { value: '{{team}}' } });
    fireEvent.change(screen.getByLabelText('sample first_name'), { target: { value: 'Ada' } });
    expect(await screen.findByText(/Detected variables:/)).toBeInTheDocument();
    expect(await screen.findByText(/Subject preview:/)).toBeInTheDocument();
    fireEvent.change(screen.getByPlaceholderText('to@example.com'), { target: { value: 'x@example.com' } });
    fireEvent.click(screen.getByText('Send test email'));
    expect(await screen.findByText(/sent via resend/)).toBeInTheDocument();
  });
  it('invalid variables json warning renders', async()=>{
    render(<MemoryRouter><AdminEmailTemplateEditorPage/></MemoryRouter>);
    await waitFor(()=>screen.getByText('New Email Template'));
    fireEvent.change(screen.getByLabelText('variables json'), { target: { value: '{bad' } });
    expect(await screen.findByText('Variables JSON is invalid.')).toBeInTheDocument();
  });
});
