import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ReportsPage } from '@/pages/ReportsPage';

vi.mock('@/hooks/useApi', () => ({ useReports: () => ({ data:[{id:'r1',title:'R1'}] }), useReport: () => ({ data:{id:'r1', title:'R1', markdown_content:'md', source_refs:[], prompt:'p', created_at:'x'} }), useCreateReport: () => ({ mutateAsync: vi.fn(async()=>({id:'r1'})) }) }));
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));

describe('reports page', () => { it('renders download link', () => { render(<ReportsPage/>); expect(screen.getByText('Download report').getAttribute('href')).toContain('/reports/r1/download'); }); });
