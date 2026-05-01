import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ReportsPage } from '@/pages/ReportsPage';

const mockUseReport = vi.fn();

vi.mock('@/hooks/useApi', () => ({
  useReports: () => ({ data: [{ id: 'r1', title: 'R1' }] }),
  useReport: (...args: unknown[]) => mockUseReport(...args),
  useCreateReport: () => ({ mutateAsync: vi.fn(async () => ({ id: 'r1' })) }),
  useUpdateReport: () => ({ mutateAsync: vi.fn(), isPending: false }),
}));

vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));

describe('reports page', () => {
  beforeEach(() => {
    mockUseReport.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it('renders structured sections when present', () => {
    mockUseReport.mockReturnValue({
      data: {
        id: 'r1',
        title: 'R1',
        markdown_content: 'markdown fallback',
        source_refs: [],
        prompt: 'p',
        created_at: 'x',
        sections: {
          executive_summary: 'Executive summary content',
          timeline_analysis: 'Timeline analysis content',
          relationship_analysis: 'Relationship analysis content',
        },
      },
    });

    render(<ReportsPage />);

    expect(screen.getByText('Executive Summary / Summary')).toBeInTheDocument();
    expect(screen.getByText('Executive summary content')).toBeInTheDocument();
    expect(screen.getByText('Timeline Analysis')).toBeInTheDocument();
    expect(screen.getByText('Relationship Analysis')).toBeInTheDocument();
    expect(screen.queryByText('markdown fallback')).not.toBeInTheDocument();
  });

  it('renders markdown fallback when sections are missing', () => {
    mockUseReport.mockReturnValue({
      data: { id: 'r1', title: 'R1', markdown_content: 'md fallback', source_refs: [], prompt: 'p', created_at: 'x' },
    });

    render(<ReportsPage />);

    expect(screen.getByText('md fallback')).toBeInTheDocument();
    expect(screen.queryByText('Executive Summary / Summary')).not.toBeInTheDocument();
  });

  it('shows markdown and pdf download actions', () => {
    mockUseReport.mockReturnValue({
      data: { id: 'r1', title: 'R1', markdown_content: 'md', source_refs: [], prompt: 'p', created_at: 'x' },
    });

    render(<ReportsPage />);

    expect(screen.getByText('Download Markdown').getAttribute('href')).toContain('/reports/r1/download?format=md');
    expect(screen.getByText('Download PDF').getAttribute('href')).toContain('/reports/r1/download?format=pdf');
  });

  it('renders long section content without breaking', () => {
    const longContent = 'verylongword'.repeat(150);
    mockUseReport.mockReturnValue({
      data: {
        id: 'r1',
        title: 'R1',
        markdown_content: 'md',
        source_refs: [],
        prompt: 'p',
        created_at: 'x',
        sections: {
          summary: longContent,
        },
      },
    });

    render(<ReportsPage />);

    expect(screen.getByText(longContent)).toBeInTheDocument();
  });
});
