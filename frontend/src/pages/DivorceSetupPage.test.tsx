import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { DivorceSetupPage } from './DivorceSetupPage';

const nav = vi.hoisted(() => vi.fn());
const create = vi.hoisted(() => vi.fn().mockResolvedValue({ id: 'ws1' }));
vi.mock('react-router-dom', async (orig) => ({ ...(await orig() as object), useNavigate: () => nav }));
vi.mock('@/services/api', () => ({ api: { createDivorceWorkspace: create } }));

describe('DivorceSetupPage', () => {
  it('creates workspace and redirects to /divorce', async () => {
    render(<MemoryRouter><DivorceSetupPage /></MemoryRouter>);
    fireEvent.change(screen.getByPlaceholderText('Case title'), { target: { value: 'Case A' } });
    fireEvent.change(screen.getByPlaceholderText('Jurisdiction'), { target: { value: 'CA' } });
    fireEvent.click(screen.getByText('Create'));
    await waitFor(() => expect(nav).toHaveBeenCalledWith('/divorce'));
  });
});
