import { DivorceDashboardPage } from '@/pages/DivorceDashboardPage';
import { DivorceSetupPage } from '@/pages/DivorceSetupPage';
import { DivorceTimelinePage } from '@/pages/DivorceTimelinePage';
import { DivorceReportsPage } from '@/pages/DivorceReportsPage';
import { DivorceTasksPage } from '@/pages/DivorceTasksPage';
import { DivorceCommunicationsPage } from '@/pages/DivorceCommunicationsPage';
import { createBrowserRouter } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { TimelinePage } from '@/pages/TimelinePage';
import { DocumentsPage } from '@/pages/DocumentsPage';
import { DocumentDetailPage } from '@/pages/DocumentDetailPage';
import { SearchPage } from '@/pages/SearchPage';
import { QueuePage } from '@/pages/QueuePage';
import { CategoriesPage } from '@/pages/CategoriesPage';
import { InsightsPage } from '@/pages/InsightsPage';
import { ConnectionsPage } from '@/pages/ConnectionsPage';
import { ReviewQueuePage } from '@/pages/ReviewQueuePage';
import { ConnectionCallbackPage } from '@/pages/ConnectionCallbackPage';
import { LoginPage } from '@/pages/auth/LoginPage';
import { RegisterPage } from '@/pages/auth/RegisterPage';
import { RequireAuth } from '@/components/auth/RequireAuth';
import { DashboardPage } from '@/pages/DashboardPage';
import { ActionItemsPage } from '@/pages/ActionItemsPage';
import { RelationshipReviewPage } from '@/pages/RelationshipReviewPage';
import { Navigate } from 'react-router-dom';
import { RequireAdmin } from '@/components/auth/RequireAdmin';
import { ReportsPage } from '@/pages/ReportsPage';
import { ChatPage } from '@/pages/ChatPage';
import { PricingPage } from '@/pages/PricingPage';
import { SettingsLayoutPage } from '@/pages/settings/SettingsLayoutPage';
import { SettingsAccountPage } from '@/pages/settings/SettingsAccountPage';
import { SettingsBillingPage } from '@/pages/settings/SettingsBillingPage';
import { SettingsUsagePage } from '@/pages/settings/SettingsUsagePage';
import { MessagesPage } from '@/pages/MessagesPage';
import { NotificationsPage } from '@/pages/NotificationsPage';
import { AdminMessagesPage } from '@/pages/AdminMessagesPage';
import { WorkspacesPage } from '@/pages/WorkspacesPage';
import { WorkspaceDetailPage } from '@/pages/WorkspaceDetailPage';
import { WorkspaceInviteAcceptPage } from '@/pages/WorkspaceInviteAcceptPage';
import { MySystemIntelligenceSubmissionsPage } from '@/pages/MySystemIntelligenceSubmissionsPage';

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    path: '/',
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'setup/divorce', element: <DivorceSetupPage /> },
      { path: 'divorce', element: <DivorceDashboardPage /> },
      { path: 'divorce/timeline', element: <DivorceTimelinePage /> },
      { path: 'divorce/reports', element: <DivorceReportsPage /> },
      { path: 'divorce/tasks', element: <DivorceTasksPage /> },
      { path: 'divorce/communications', element: <DivorceCommunicationsPage /> },
      { path: 'timeline', element: <TimelinePage /> },
      { path: 'documents', element: <DocumentsPage /> },
      { path: 'documents/:id', element: <DocumentDetailPage /> },
      { path: 'documents/:id/intelligence', element: <DocumentDetailPage /> },
      { path: 'search', element: <SearchPage /> },
      { path: 'queue', element: <QueuePage /> },
      { path: 'review', element: <ReviewQueuePage /> },
      { path: 'review/relationships', element: <RelationshipReviewPage /> },
      { path: 'action-items', element: <ActionItemsPage /> },
      { path: 'categories', element: <CategoriesPage /> },
      { path: 'insights', element: <InsightsPage /> },
      { path: 'connections', element: <ConnectionsPage /> },
      { path: 'chat', element: <ChatPage /> },
      { path: 'reports', element: <ReportsPage /> },
      { path: 'messages', element: <MessagesPage /> },
      { path: 'notifications', element: <NotificationsPage /> },
      { path: 'pricing', element: <PricingPage /> },
      { path: 'upgrade', element: <PricingPage /> },
      { path: 'billing', element: <PricingPage /> },
      { path: 'workspaces', element: <WorkspacesPage /> },
      { path: 'workspaces/:workspaceId', element: <WorkspaceDetailPage /> },
      { path: 'workspaces/invites/:token/accept', element: <WorkspaceInviteAcceptPage /> },
      { path: 'system-intelligence/submissions', element: <MySystemIntelligenceSubmissionsPage /> },
      {
        path: 'settings',
        element: <SettingsLayoutPage />,
        children: [
          { index: true, element: <SettingsAccountPage /> },
          { path: 'account', element: <SettingsAccountPage /> },
          { path: 'billing', element: <SettingsBillingPage /> },
          { path: 'usage', element: <SettingsUsagePage /> },
        ],
      },
      { path: 'connections/callback', element: <ConnectionCallbackPage /> },
      {
        path: 'admin',
        element: <RequireAdmin><AdminSettingsLayout /></RequireAdmin>,
        children: [
          { index: true, element: <AdminPage /> },
          { path: 'users', element: <AdminUsersPage /> },
          { path: 'users/:userId/usage', element: <AdminUserUsagePage /> },
          { path: 'subscriptions', element: <Navigate to='/admin/settings/plans' replace /> },
          { path: 'billing', element: <Navigate to='/admin/settings/billing' replace /> },
          { path: 'audit', element: <Navigate to='/admin/settings/audit' replace /> },
          { path: 'chatbot-settings', element: <Navigate to='/admin/settings/chatbot' replace /> },
          { path: 'prompts', element: <Navigate to='/admin/settings/prompts' replace /> },
          { path: 'prompts/audit', element: <Navigate to='/admin/settings/prompts/audit' replace /> },
          { path: 'prompts/analytics', element: <Navigate to='/admin/settings/prompts/analytics' replace /> },
          { path: 'settings', element: <Navigate to='/admin/settings/system' replace /> },
          { path: 'settings/system', element: <AdminSystemPage /> },
          { path: 'settings/billing', element: <AdminBillingPage /> },
          { path: 'settings/plans', element: <AdminPlansPage /> },
          { path: 'settings/llm', element: <AdminLlmProvidersPage /> },
          { path: 'settings/chatbot', element: <AdminChatbotSettingsPage /> },
          { path: 'settings/prompts', element: <AdminPromptTemplatesPage /> },
          { path: 'settings/prompts/audit', element: <AdminPromptAuditPage /> },
          { path: 'settings/prompts/analytics', element: <AdminPromptAnalyticsPage /> },
          { path: 'settings/audit', element: <AdminAuditPage /> },
          { path: 'settings/email', element: <AdminEmailSettingsPage /> },
          { path: 'settings/email/templates', element: <AdminEmailTemplatesPage /> },
          { path: 'settings/email/templates/new', element: <AdminEmailTemplateEditorPage /> },
          { path: 'settings/email/templates/:templateId', element: <AdminEmailTemplateEditorPage /> },
          { path: 'settings/email/campaigns', element: <AdminEmailCampaignsPage /> },
          { path: 'settings/email/campaigns/new', element: <AdminEmailCampaignEditorPage /> },
          { path: 'settings/email/campaigns/:campaignId', element: <AdminEmailCampaignEditorPage /> },
          { path: 'settings/email/suppressions', element: <AdminEmailSuppressionsPage /> },
          { path: 'settings/email/logs', element: <AdminEmailSendLogsPage /> },
          { path: 'settings/system-intelligence', element: <AdminSystemIntelligencePage /> },
          { path: 'messages', element: <AdminMessagesPage /> },
        ],
      },
    ],
  },
]);

import { AdminUserUsagePage, AdminBillingPage, AdminAuditPage, AdminSystemPage, AdminPlansPage, AdminLlmProvidersPage } from '@/pages/AdminSettingsPage';
import { AdminSettingsLayout } from '@/pages/admin/AdminSettingsLayout';
import { AdminPromptTemplatesPage } from '@/pages/AdminPromptTemplatesPage';
import { AdminPromptAuditPage } from '@/pages/AdminPromptAuditPage';
import { AdminPromptAnalyticsPage } from '@/pages/AdminPromptAnalyticsPage';
import { AdminChatbotSettingsPage } from '@/pages/AdminChatbotSettingsPage';
import { AdminUsersPage } from '@/pages/AdminUsersPage';
import { AdminPage } from '@/pages/AdminPage';
import { AdminEmailSettingsPage } from '@/pages/AdminEmailSettingsPage';
import { AdminEmailTemplatesPage } from '@/pages/AdminEmailTemplatesPage';
import { AdminEmailTemplateEditorPage } from '@/pages/AdminEmailTemplateEditorPage';
import { AdminEmailCampaignsPage } from '@/pages/AdminEmailCampaignsPage';
import { AdminEmailCampaignEditorPage } from '@/pages/AdminEmailCampaignEditorPage';
import { AdminEmailSuppressionsPage } from '@/pages/AdminEmailSuppressionsPage';
import { AdminEmailSendLogsPage } from '@/pages/AdminEmailSendLogsPage';
import { AdminSystemIntelligencePage } from '@/pages/AdminSystemIntelligencePage';
