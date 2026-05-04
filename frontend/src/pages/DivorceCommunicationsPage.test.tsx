import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { DivorceCommunicationsPage } from './DivorceCommunicationsPage';

vi.mock('@/services/api', () => ({ api: {
  listDivorceCommunications: vi.fn().mockResolvedValue([{id:'c1',sender:'a',recipient:'b',subject:'s',sent_at:'2026-05-01',category:'court',tone:'urgent',review_status:'suggested',metadata_json:{source_snippet:'quoted'},extracted_issues_json:{legal:['court']},extracted_deadlines_json:['by friday'],extracted_offers_json:[],extracted_allegations_json:[]}]),
  extractDivorceCommunications: vi.fn().mockResolvedValue({created_count:1}),
  acceptDivorceCommunication: vi.fn().mockResolvedValue({}),
  rejectDivorceCommunication: vi.fn().mockResolvedValue({}),
  deleteDivorceCommunication: vi.fn().mockResolvedValue({deleted:true}),
} }));

describe('DivorceCommunicationsPage', ()=>{
  it('renders suggested communications and actions', async ()=>{
    localStorage.setItem('activeWorkspaceId','ws1');
    render(<QueryClientProvider client={new QueryClient()}><DivorceCommunicationsPage/></QueryClientProvider>);
    expect(await screen.findByText('Suggested communications (1)')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Extract communications'));
    fireEvent.click(screen.getByText('Accept'));
  });
});
