import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AdminUsersPage } from './AdminUsersPage';

const hooks = vi.hoisted(() => ({
  useAdminUsers: vi.fn(), useAdminInvites: vi.fn(), useCreateAdminUser: vi.fn(), useInviteAdminUser: vi.fn(), useUpdateUserRole: vi.fn(),
  useDeactivateAdminUser: vi.fn(), useReactivateAdminUser: vi.fn(), useDeleteAdminUser: vi.fn(), useResendAdminInvite: vi.fn(), useCancelAdminInvite: vi.fn(),
}));
vi.mock('@/hooks/useApi', () => hooks);
vi.mock('@/store/uiStore', () => ({ useUIStore: () => ({ pushToast: vi.fn() }) }));

function renderPage() { return render(<MemoryRouter><AdminUsersPage /></MemoryRouter>); }

describe('AdminUsersPage', () => {
  afterEach(() => cleanup());
  const mutateAsync = vi.fn().mockResolvedValue({});
  beforeEach(() => {
    vi.clearAllMocks();
    hooks.useAdminUsers.mockReturnValue({ isLoading: false, isError: false, data: { items: [{ id: 'u1', email: 'a@test.com', display_name: 'A', role: 'viewer', is_active: true, created_at: '2026-01-01T00:00:00Z' }] } });
    hooks.useAdminInvites.mockReturnValue({ isLoading: false, isError: false, data: [{ id: 'i1', email: 'i@test.com', role: 'viewer', status: 'pending', dev_invite_link: 'http://localhost/invite' }] });
    hooks.useCreateAdminUser.mockReturnValue({ mutateAsync }); hooks.useInviteAdminUser.mockReturnValue({ mutateAsync }); hooks.useUpdateUserRole.mockReturnValue({ mutateAsync });
    hooks.useDeactivateAdminUser.mockReturnValue({ mutateAsync }); hooks.useReactivateAdminUser.mockReturnValue({ mutateAsync }); hooks.useDeleteAdminUser.mockReturnValue({ mutateAsync }); hooks.useResendAdminInvite.mockReturnValue({ mutateAsync }); hooks.useCancelAdminInvite.mockReturnValue({ mutateAsync });
  });

  it('renders table and filters call query hook', () => {
    renderPage();
    expect(screen.getByText('a@test.com')).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Search users'), { target: { value: 'alice' } });
    expect(hooks.useAdminUsers).toHaveBeenLastCalledWith(0, 100, expect.objectContaining({ q: 'alice' }));
  });

  it('create/invite modals submit API', async () => {
    renderPage();
    fireEvent.click(screen.getAllByText('Create User')[0]);
    fireEvent.change(screen.getByPlaceholderText('Email'), { target: { value: 'new@test.com' } });
    fireEvent.change(screen.getByPlaceholderText('Display name'), { target: { value: 'New' } });
    fireEvent.click(screen.getByText('Submit'));
    expect(mutateAsync).toHaveBeenCalled();

    fireEvent.click(screen.getAllByText('Invite User')[0]);
    fireEvent.change(screen.getAllByPlaceholderText('Email')[0], { target: { value: 'inv@test.com' } });
  });

  it('role/deactivate/delete/resend/cancel actions call APIs and require delete confirmation', async () => {
    renderPage();
    fireEvent.change(screen.getAllByLabelText('Role for a@test.com')[0], { target: { value: 'admin' } });
    fireEvent.click(screen.getAllByText('Deactivate')[0]);
    fireEvent.click(screen.getAllByText('Delete')[0]);
    const delBtn = screen.getAllByRole('button', { name: 'Delete' })[1];
    expect(delBtn).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Delete confirmation'), { target: { value: 'delete a@test.com' } });
    expect(delBtn).not.toBeDisabled();
    fireEvent.click(screen.getByText('Resend'));
    fireEvent.click(screen.getAllByText('Cancel')[0]);
    expect(mutateAsync).toHaveBeenCalled();
  });
});
