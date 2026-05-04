import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, test, vi } from 'vitest';
import { LoginPage } from '@/pages/auth/LoginPage';

const mockLogin = vi.fn();
const mockGetAuthConfig = vi.fn();
vi.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ user: null, login: mockLogin }) }));
vi.mock('@/services/api', () => ({ api: { getAuthConfig: mockGetAuthConfig } }));

test('login form submits credentials', async () => {
  mockGetAuthConfig.mockResolvedValue({ google_login_enabled: false });
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

test('google login button hidden when disabled', async () => {
  mockGetAuthConfig.mockResolvedValue({ google_login_enabled: false });
  render(<MemoryRouter><LoginPage /></MemoryRouter>);
  await waitFor(() => expect(mockGetAuthConfig).toHaveBeenCalled());
  expect(screen.queryByText('Continue with Google')).toBeNull();
});

test('google login button visible when enabled', async () => {
  mockGetAuthConfig.mockResolvedValue({ google_login_enabled: true });
  render(<MemoryRouter><LoginPage /></MemoryRouter>);
  expect(await screen.findByText('Continue with Google')).toBeInTheDocument();
});
