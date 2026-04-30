import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { RequireAdmin } from '@/components/auth/RequireAdmin';

vi.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ user: { email: 'v@example.com', role: 'viewer' }, loading: false, logout: vi.fn() }) }));

describe('admin guard', () => {
  it('blocks non-admin', () => {
    render(<MemoryRouter><RequireAdmin><div>ok</div></RequireAdmin></MemoryRouter>);
    expect(screen.getByText(/Unauthorized/)).toBeInTheDocument();
  });
});
