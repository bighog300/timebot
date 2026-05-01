import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReportsPage } from './ReportsPage';

vi.mock('@/hooks/useApi', () => ({
  useReports: vi.fn(),
  useReport: vi.fn(),
  useCreateReport: vi.fn(),
  useUpdateReport: vi.fn(),
}));

vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));
vi.mock('@/services/api', () => ({ api: { getReportDownloadUrl: vi.fn(() => '/api/v1/reports/r1/download') }, getErrorDetail: () => 'error' }));

import { useReports, useReport, useCreateReport, useUpdateReport } from '@/hooks/useApi';

const baseReport = {
  id: 'r1',
  title: 'Report',
  prompt: 'p',
  markdown_content: '# md',
  sections: { summary: 'Summary A', timeline: 'Timeline A', relationships: 'Relationships A' },
  source_refs: [],
  created_at: new Date().toISOString(),
};

describe('ReportsPage section editing', () => {
  beforeEach(() => {
    vi.mocked(useReports).mockReturnValue({ data: [baseReport] } as never);
    vi.mocked(useCreateReport).mockReturnValue({ mutateAsync: vi.fn() } as never);
    vi.mocked(useUpdateReport).mockReturnValue({ mutateAsync: vi.fn().mockResolvedValue(baseReport), isPending: false } as never);
  });
  afterEach(() => {
    cleanup();
  });

  it('shows edit controls for structured sections', async () => {
    vi.mocked(useReport).mockReturnValue({ data: baseReport } as never);
    render(<ReportsPage />);
    await userEvent.click(screen.getAllByRole('button', { name: 'Report' })[0]);
    expect(screen.getAllByRole('button', { name: 'Edit' }).length).toBeGreaterThan(0);
  });

  it('save calls update endpoint', async () => {
    vi.mocked(useReport).mockReturnValue({ data: baseReport } as never);
    const updateSpy = vi.fn().mockResolvedValue(baseReport);
    vi.mocked(useUpdateReport).mockReturnValue({ mutateAsync: updateSpy, isPending: false } as never);
    render(<ReportsPage />);
    await userEvent.click(screen.getAllByRole('button', { name: 'Report' })[0]);
    await userEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0]);
    const textarea = screen.getAllByRole('textbox').at(-1)!;
    await userEvent.clear(textarea);
    await userEvent.type(textarea, 'Updated summary');
    await userEvent.click(screen.getByRole('button', { name: 'Save' }));
    expect(updateSpy).toHaveBeenCalled();
  });

  it('cancel restores previous content', async () => {
    vi.mocked(useReport).mockReturnValue({ data: baseReport } as never);
    render(<ReportsPage />);
    await userEvent.click(screen.getAllByRole('button', { name: 'Report' })[0]);
    await userEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0]);
    const textarea = screen.getAllByRole('textbox').at(-1)!;
    await userEvent.clear(textarea);
    await userEvent.type(textarea, 'Changed');
    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(screen.getByText('Summary A')).toBeTruthy();
  });

  it('does not show edit controls for markdown-only reports', async () => {
    vi.mocked(useReport).mockReturnValue({ data: { ...baseReport, sections: null } } as never);
    render(<ReportsPage />);
    await userEvent.click(screen.getAllByRole('button', { name: 'Report' })[0]);
    expect(screen.queryByRole('button', { name: 'Edit' })).toBeNull();
  });

  it('renders wrapped download actions and markdown fallback', async () => {
    vi.mocked(useReport).mockReturnValue({ data: { ...baseReport, sections: null, markdown_content: 'Long markdown content line' } } as never);
    render(<ReportsPage />);
    await userEvent.click(screen.getAllByRole('button', { name: 'Report' })[0]);
    const actions = screen.getByRole('link', { name: 'Download Markdown' }).parentElement;
    expect(actions?.className).toContain('flex-wrap');
    expect(screen.getByText('Long markdown content line').closest('pre')?.className).toContain('overflow-x-auto');
    expect(screen.getByRole('link', { name: 'Download PDF' })).toBeTruthy();
  });

  it('keeps section editor textarea usable and wrapped on mobile', async () => {
    vi.mocked(useReport).mockReturnValue({ data: baseReport } as never);
    render(<ReportsPage />);
    await userEvent.click(screen.getAllByRole('button', { name: 'Report' })[0]);
    await userEvent.click(screen.getAllByRole('button', { name: 'Edit' })[0]);
    const textarea = screen.getAllByRole('textbox').at(-1)!;
    expect(textarea.className).toContain('min-h-40');
    expect(screen.getByRole('button', { name: 'Save' }).parentElement?.className).toContain('flex-wrap');
  });
});
