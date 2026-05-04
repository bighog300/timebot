import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, vi } from 'vitest';
import { AdminEmailSendLogsPage } from '@/pages/AdminEmailSendLogsPage';
import { api } from '@/services/api';

vi.mock('@/services/api', async () => ({
  ...(await vi.importActual('@/services/api')),
  api: { getEmailSendLogs: vi.fn().mockResolvedValue([{id:'1',provider:'resend',recipient_email:'a@b.com',subject:'Sub',status:'sent',provider_message_id:'m',error_message_sanitized:null,created_at:'2020',sent_at:'2020',failed_at:null}]) },
}));

describe('AdminEmailSendLogsPage', () => {
  it('renders send logs rows', async () => {
    render(<MemoryRouter><AdminEmailSendLogsPage /></MemoryRouter>);
    expect(await screen.findByText('Email Send Logs')).toBeInTheDocument();
    expect(await screen.findByText('a@b.com')).toBeInTheDocument();
    expect(api.getEmailSendLogs).toHaveBeenCalled();
  });
});
