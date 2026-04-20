import { RouterProvider } from 'react-router-dom';
import { router } from '@/app/router';
import { useLiveEvents } from '@/hooks/useLiveEvents';

export function App() {
  useLiveEvents();
  return <RouterProvider router={router} />;
}
