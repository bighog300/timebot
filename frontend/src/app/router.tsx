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

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <TimelinePage /> },
      { path: 'documents', element: <DocumentsPage /> },
      { path: 'documents/:id', element: <DocumentDetailPage /> },
      { path: 'search', element: <SearchPage /> },
      { path: 'queue', element: <QueuePage /> },
      { path: 'review', element: <ReviewQueuePage /> },
      { path: 'categories', element: <CategoriesPage /> },
      { path: 'insights', element: <InsightsPage /> },
      { path: 'connections', element: <ConnectionsPage /> },
    ],
  },
]);
