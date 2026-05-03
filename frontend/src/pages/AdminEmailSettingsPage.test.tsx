import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, test, expect } from 'vitest';
import { AdminEmailSettingsPage } from './AdminEmailSettingsPage';

const { apiMock } = vi.hoisted(() => ({
  apiMock: {
    listEmailProviderConfigs: vi.fn(async()=>[{provider:'resend',enabled:true,from_email:'noreply@example.com',configured:true,created_at:'',updated_at:''}]),
    patchEmailProviderConfig: vi.fn(),
    testSendEmail: vi.fn(async()=>({status:'sent',provider:'resend',log_id:'1'})),
    getEmailSendLogs: vi.fn(async()=>[{id:'1',provider:'resend',recipient_email:'a@b.com',from_email:'noreply@example.com',subject:'s',status:'sent',created_at:''}])
  }
}));
vi.mock('@/services/api', ()=>({api:apiMock,getErrorDetail:()=> 'bad'}));

test('renders and submits test email', async ()=>{
  render(<MemoryRouter><AdminEmailSettingsPage /></MemoryRouter>);
  expect(await screen.findByText('Send test email')).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('to email'),{target:{value:'a@b.com'}});
  fireEvent.click(screen.getByText('Send'));
  await waitFor(()=>expect(apiMock.testSendEmail).toHaveBeenCalled());
  expect(await screen.findByText(/status:sent/)).toBeInTheDocument();
});
