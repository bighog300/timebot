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
import { AdminPage } from '@/pages/AdminPage';
import { AdminChatbotSettingsPage } from '@/pages/AdminChatbotSettingsPage';
import { ReportsPage } from '@/pages/ReportsPage';
import { ChatPage } from '@/pages/ChatPage';
import { AdminPromptTemplatesPage } from '@/pages/AdminPromptTemplatesPage';
import { PricingPage } from '@/pages/PricingPage';

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
      { path: 'connections/callback', element: <ConnectionCallbackPage /> },
      { path: 'admin', element: <RequireAdmin><AdminPage /></RequireAdmin> },
      { path: 'admin/chatbot-settings', element: <RequireAdmin><AdminChatbotSettingsPage /></RequireAdmin> },
      { path: 'admin/prompts', element: <RequireAdmin><AdminPromptTemplatesPage /></RequireAdmin> },
    ],
  },
]);
