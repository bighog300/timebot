import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { expect, test, vi } from 'vitest';
import { RequireAuth } from '@/components/auth/RequireAuth';

const mockUseAuth = vi.fn();
vi.mock('@/auth/AuthContext', () => ({ useAuth: () => mockUseAuth() }));

test('redirects unauthenticated users to login', () => {
  mockUseAuth.mockReturnValue({ user: null, loading: false });
  render(
    <MemoryRouter initialEntries={['/private']}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route
          path="/private"
          element={
            <RequireAuth>
              <div>Private Page</div>
            </RequireAuth>
          }
        />
      </Routes>
    </MemoryRouter>,
  );

  expect(screen.getByText('Login Page')).toBeInTheDocument();
});
