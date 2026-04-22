import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test, vi } from 'vitest';
import { LoginPage } from '@/pages/auth/LoginPage';

const mockLogin = vi.fn();
vi.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ user: null, login: mockLogin }) }));

test('login form submits credentials', async () => {
  mockLogin.mockResolvedValue(undefined);
  render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  );

  fireEvent.change(screen.getByPlaceholderText('Email'), { target: { value: 'user@example.com' } });
  fireEvent.change(screen.getByPlaceholderText('Password'), { target: { value: 'password123' } });
  fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

  await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('user@example.com', 'password123'));
});
