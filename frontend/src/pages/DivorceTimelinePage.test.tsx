import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DivorceTimelinePage } from './DivorceTimelinePage';
vi.mock('@/services/api', () => ({ api: { listDivorceTimeline: vi.fn(async()=>[{id:'1',workspace_id:'w',event_date:'2026-01-01',date_precision:'exact',title:'Event',category:'legal',review_status:'suggested',include_in_report:true,confidence:0.8,source_snippet:'snippet'}]), extractDivorceTimeline: vi.fn(async()=>({created_count:1})), acceptDivorceTimeline: vi.fn(async()=>({})), rejectDivorceTimeline: vi.fn(async()=>({})), createDivorceTimelineManual: vi.fn(async()=>({})) } }));

describe('DivorceTimelinePage', () => {
  it('renders and shows source snippet', async () => {
    localStorage.setItem('active_workspace_id', 'w');
    render(<QueryClientProvider client={new QueryClient()}><DivorceTimelinePage /></QueryClientProvider>);
    expect(await screen.findByText(/AI-suggested chronology/i)).toBeTruthy();
    expect(await screen.findByText('snippet')).toBeTruthy();
    fireEvent.click(screen.getByText('Extract timeline'));
    fireEvent.click(screen.getByText('Accept'));
    fireEvent.click(screen.getByText('Reject'));
  });
});
