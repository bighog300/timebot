import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, it, vi, expect, afterEach } from 'vitest';
import { AdminEmailCampaignsPage } from '@/pages/AdminEmailCampaignsPage';
import { AdminEmailCampaignEditorPage } from '@/pages/AdminEmailCampaignEditorPage';
vi.mock('@/services/api', ()=>({ api:{
  listEmailCampaigns: vi.fn(async()=>[{id:'1',name:'C',template_id:'t1',audience_type:'all_users',status:'draft',updated_at:'now',created_at:'now'}]),
  listEmailTemplates: vi.fn(async()=>[{id:'t1',name:'T'}]),
  createEmailCampaign: vi.fn(async(p)=>({id:'2',...p,updated_at:'',created_at:''})),
  getEmailCampaign: vi.fn(async()=>({id:'1',name:'C',template_id:'t1',audience_type:'all_users',status:'draft',variables_json:{},updated_at:'',created_at:''})),
  patchEmailCampaign: vi.fn(), archiveEmailCampaign: vi.fn(), previewEmailCampaign: vi.fn(async()=>({subject:'s',preheader:'p',html_body:'h',text_body:'t',missing_variables:[]})), previewCampaignRecipients: vi.fn(async()=>({total_candidates:10,sendable_count:7,suppressed_count:1,invalid_count:1,duplicate_count:1,sample_recipients:['a@b.com'],suppressed_samples:['s@b.com'],invalid_samples:['bad']})), sendCampaign: vi.fn(async()=>({total_candidates:10,sendable_count:7,sent_count:7,failed_count:0,skipped_count:3})), testSendCampaign: vi.fn(async()=>({status:'sent'}))
}, getErrorDetail: ()=> 'err'}));

afterEach(() => cleanup());

describe('campaign pages',()=>{
  it('list renders', async()=>{render(<MemoryRouter><AdminEmailCampaignsPage/></MemoryRouter>); expect(await screen.findByText('C')).toBeInTheDocument();});
  it('editor preview and test send', async()=>{render(<MemoryRouter initialEntries={['/admin/settings/email/campaigns/1']}><Routes><Route path='/admin/settings/email/campaigns/:campaignId' element={<AdminEmailCampaignEditorPage/>}/></Routes></MemoryRouter>); await waitFor(()=>screen.getByText('Edit Email Campaign')); fireEvent.click(screen.getByText('Preview')); fireEvent.click(screen.getByText('Preview recipients')); fireEvent.change(screen.getByLabelText('to email'),{target:{value:'a@b.com'}}); fireEvent.click(screen.getByText('Send test')); expect(await screen.findByText(/total candidates 10/)).toBeInTheDocument();});
  it('send button disabled until confirmation matches', async()=>{render(<MemoryRouter initialEntries={['/admin/settings/email/campaigns/1']}><Routes><Route path='/admin/settings/email/campaigns/:campaignId' element={<AdminEmailCampaignEditorPage/>}/></Routes></MemoryRouter>); const btn=await screen.findByRole('button',{name:'Send campaign'}); expect(btn).toBeDisabled(); fireEvent.change(screen.getByLabelText('campaign confirmation'), {target:{value:'SEND CAMPAIGN'}}); expect(btn).toBeDisabled();});
});
