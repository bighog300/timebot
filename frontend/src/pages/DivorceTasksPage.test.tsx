import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DivorceTasksPage } from './DivorceTasksPage';
import { vi } from 'vitest';

vi.mock('@/services/api', () => ({ api: {
  listDivorceTasks: vi.fn().mockResolvedValue([{id:'1',content:'Task',status:'suggested',priority:'high',category:'legal'}]),
  extractDivorceTasks: vi.fn().mockResolvedValue({created_count:1}),
  acceptDivorceTask: vi.fn().mockResolvedValue({}),
  rejectDivorceTask: vi.fn().mockResolvedValue({}),
  patchDivorceTask: vi.fn().mockResolvedValue({}),
} }));

describe('DivorceTasksPage', ()=>{
  it('renders suggested tasks and extract button', async ()=>{
    localStorage.setItem('activeWorkspaceId','ws1');
    render(<QueryClientProvider client={new QueryClient()}><DivorceTasksPage/></QueryClientProvider>);
    expect(await screen.findByText('Suggested tasks (1)')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Extract tasks from documents'));
  });
});
