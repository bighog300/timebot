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
      { path: 'pricing', element: <PricingPage /> },
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
        element: <RequireAdmin><AdminSettingsPage /></RequireAdmin>,
        children: [
          { index: true, element: <Navigate to='/admin/subscriptions' replace /> },
          { path: 'subscriptions', element: <AdminSubscriptionsPage /> },
          { path: 'users', element: <AdminUsersPage /> },
          { path: 'users/:userId/usage', element: <AdminUserUsagePage /> },
          { path: 'billing', element: <AdminBillingPage /> },
          { path: 'audit', element: <AdminAuditPage /> },
          { path: 'chatbot-settings', element: <AdminChatbotSettingsPage /> },
          { path: 'prompts', element: <AdminPromptTemplatesPage /> },
          { path: 'prompts/audit', element: <AdminPromptAuditPage /> },
          { path: 'prompts/analytics', element: <AdminPromptAnalyticsPage /> },
        ],
      },
    ],
  },
]);

import { AdminSettingsPage, AdminSubscriptionsPage, AdminUserUsagePage, AdminBillingPage, AdminAuditPage } from '@/pages/AdminSettingsPage';
import { AdminPromptTemplatesPage } from '@/pages/AdminPromptTemplatesPage';
import { AdminPromptAuditPage } from '@/pages/AdminPromptAuditPage';
import { AdminPromptAnalyticsPage } from '@/pages/AdminPromptAnalyticsPage';
import { AdminChatbotSettingsPage } from '@/pages/AdminChatbotSettingsPage';
import { AdminUsersPage } from '@/pages/AdminUsersPage';
