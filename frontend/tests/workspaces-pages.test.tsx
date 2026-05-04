import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, test, vi } from 'vitest';
import { WorkspacesPage } from '@/pages/WorkspacesPage';
import { WorkspaceDetailPage } from '@/pages/WorkspaceDetailPage';
import { WorkspaceInviteAcceptPage } from '@/pages/WorkspaceInviteAcceptPage';

const mockCreate = vi.fn();
const mockInvite = vi.fn();
const mockAccept = vi.fn();
type TestWorkspace = { id: string; name: string; type: 'personal' | 'team' };
type TestWorkspaceDetail = TestWorkspace & { members?: Array<{ user_id: string; role: 'owner' | 'admin' | 'member'; email?: string | null }>; invites?: Array<{ id: string; workspace_id: string; email: string; role: string; status: string; created_at: string; dev_invite_link?: string }> };
let workspaceData: TestWorkspace[] = [];
let workspaceDetail: TestWorkspaceDetail | null = null;
let acceptState = { isPending: false, isSuccess: true, isError: false };

vi.mock('@/hooks/useApi', () => ({
  useWorkspaces: () => ({ data: workspaceData, isLoading: false, isError: false }),
  useCreateWorkspace: () => ({ mutateAsync: (...args: unknown[]) => mockCreate(...args), isPending: false }),
  useWorkspaceDetail: () => ({ data: workspaceDetail, isLoading: false, isError: false }),
  useInviteWorkspaceMember: () => ({ mutateAsync: (...args: unknown[]) => mockInvite(...args), isError: false }),
  useResendWorkspaceInvite: () => ({ mutate: vi.fn() }),
  useCancelWorkspaceInvite: () => ({ mutate: vi.fn() }),
  useUpdateWorkspaceMemberRole: () => ({ mutate: vi.fn() }),
  useRemoveWorkspaceMember: () => ({ mutate: vi.fn() }),
  useAcceptWorkspaceInvite: () => ({ mutate: (...args: unknown[]) => mockAccept(...args), ...acceptState }),
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useParams: () => ({ workspaceId: 'ws1', token: 'tok1' }), Link: ({ children }: { children: React.ReactNode }) => <a>{children}</a> };
});

vi.mock('@/auth/AuthContext', () => ({ useAuth: () => ({ user: { id: 'u1' } }) }));

function wrap(ui: React.ReactNode) { return render(<QueryClientProvider client={new QueryClient()}>{ui}</QueryClientProvider>); }

beforeEach(() => { workspaceData = [{ id: 'ws1', name: 'My Team', type: 'team' }]; workspaceDetail = { id: 'ws1', name: 'My Team', type: 'team', members: [{ user_id: 'u1', role: 'owner', email: 'o@example.com' }], invites: [{ id: 'i1', workspace_id: 'ws1', email: 'x@example.com', role: 'member', status: 'pending', created_at: '2026-01-01', dev_invite_link: '/workspaces/invites/abc/accept' }] as any }; acceptState = { isPending: false, isSuccess: true, isError: false }; mockCreate.mockReset(); mockInvite.mockReset(); mockAccept.mockReset(); });

test('workspace list renders and create flow submits', async () => {
  mockCreate.mockResolvedValue({ id: 'ws2' });
  wrap(<WorkspacesPage />);
  expect(screen.getByText('My Team')).toBeInTheDocument();
  fireEvent.change(screen.getByPlaceholderText('New team workspace'), { target: { value: 'Alpha' } });
  fireEvent.click(screen.getByText('Create team workspace'));
  await waitFor(() => expect(mockCreate).toHaveBeenCalledWith({ name: 'Alpha' }));
});

test('invite form submits and owner remove disabled', async () => {
  mockInvite.mockResolvedValue({ invite: { id: '1', email: 'x@example.com', role: 'member' }, dev_invite_link: '/workspaces/invites/abc/accept' });
  wrap(<WorkspaceDetailPage />);
  fireEvent.change(screen.getByPlaceholderText('member@example.com'), { target: { value: 'x@example.com' } });
  fireEvent.click(screen.getByText('Invite'));
  await waitFor(() => expect(mockInvite).toHaveBeenCalledWith({ email: 'x@example.com', role: 'member' }));
  expect(screen.getByText(/Dev invite link/)).toBeInTheDocument();
  expect(screen.getByText('Remove')).toBeDisabled();
});

test('accept invite page success', async () => {
  wrap(<WorkspaceInviteAcceptPage />);
  await waitFor(() => expect(mockAccept).toHaveBeenCalledWith({ token: 'tok1' }));
  expect(screen.getByText('Invite accepted successfully.')).toBeInTheDocument();
});

test('accept invite page error', () => {
  acceptState = { isPending: false, isSuccess: false, isError: true };
  wrap(<WorkspaceInviteAcceptPage />);
  expect(screen.getByText(/Failed to accept invite:/)).toBeInTheDocument();
});
