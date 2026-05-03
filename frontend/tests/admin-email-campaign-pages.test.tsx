import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, vi, expect } from 'vitest';
import { AdminEmailCampaignsPage } from '@/pages/AdminEmailCampaignsPage';
import { AdminEmailCampaignEditorPage } from '@/pages/AdminEmailCampaignEditorPage';
vi.mock('@/services/api', ()=>({ api:{
  listEmailCampaigns: vi.fn(async()=>[{id:'1',name:'C',template_id:'t1',audience_type:'all_users',status:'draft',updated_at:'now',created_at:'now'}]),
  listEmailTemplates: vi.fn(async()=>[{id:'t1',name:'T'}]),
  createEmailCampaign: vi.fn(async(p)=>({id:'2',...p,updated_at:'',created_at:''})),
  getEmailCampaign: vi.fn(async()=>({id:'1',name:'C',template_id:'t1',audience_type:'all_users',status:'draft',variables_json:{},updated_at:'',created_at:''})),
  patchEmailCampaign: vi.fn(), archiveEmailCampaign: vi.fn(), previewEmailCampaign: vi.fn(async()=>({subject:'s',preheader:'p',html_body:'h',text_body:'t',missing_variables:[]})), testSendCampaign: vi.fn(async()=>({status:'sent'}))
}, getErrorDetail: ()=> 'err'}));

describe('campaign pages',()=>{
  it('list renders', async()=>{render(<MemoryRouter><AdminEmailCampaignsPage/></MemoryRouter>); expect(await screen.findByText('C')).toBeInTheDocument();});
  it('editor preview and test send', async()=>{render(<MemoryRouter><AdminEmailCampaignEditorPage/></MemoryRouter>); await waitFor(()=>screen.getByText('New Email Campaign')); fireEvent.click(screen.getByText('Preview')); fireEvent.change(screen.getByLabelText('to email'),{target:{value:'a@b.com'}}); fireEvent.click(screen.getByText('Send test'));});
});
