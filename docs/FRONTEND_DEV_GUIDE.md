# Frontend Development Guide

## Quick Start

### Prerequisites
- Node.js 18+ and npm 9+
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
# Start dev server
npm run dev

# Opens at http://localhost:3000
```

### Environment Setup

```bash
# Copy environment template
cp .env.example .env.development

# Edit .env.development and add your OAuth credentials
```

## Project Structure Overview

```
src/
├── main.tsx              # App entry point
├── App.tsx               # Root component with routing
├── components/           # Reusable UI components
├── pages/                # Page-level components
├── features/             # Feature modules (auth, documents, timeline)
├── hooks/                # Custom React hooks
├── services/             # API service layer
├── store/                # Zustand state stores
├── types/                # TypeScript type definitions
├── utils/                # Utility functions
├── lib/                  # Third-party configurations
└── styles/               # Global styles
```

## Core Technologies

### React + TypeScript
- Modern React with hooks and functional components
- Full TypeScript for type safety
- No class components

### State Management
- **Zustand** for global state (simple, fast)
- **TanStack Query** for server state (auto-caching, refetching)
- **React Hook Form** for form state

### Styling
- **Tailwind CSS** for utility-first styling
- **Framer Motion** for animations
- **Radix UI** for accessible component primitives

### Build Tool
- **Vite** for fast development and optimized builds

## Development Workflow

### 1. Create a New Component

```typescript
// src/components/example/MyComponent.tsx

import { FC } from 'react';
import { motion } from 'framer-motion';

interface MyComponentProps {
  title: string;
  onAction?: () => void;
}

export const MyComponent: FC<MyComponentProps> = ({ title, onAction }) => {
  return (
    <motion.div
      className="p-4 bg-bg-tertiary rounded-lg"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <h3 className="text-lg font-semibold text-text-primary">{title}</h3>
      {onAction && (
        <button
          onClick={onAction}
          className="mt-2 px-4 py-2 bg-accent-primary rounded"
        >
          Action
        </button>
      )}
    </motion.div>
  );
};
```

### 2. Create a Custom Hook

```typescript
// src/hooks/useDocuments.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsService } from '@/services/documents.service';
import { Document } from '@/types/document.types';

export const useDocuments = () => {
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['documents'],
    queryFn: documentsService.getAll,
  });

  const uploadMutation = useMutation({
    mutationFn: documentsService.upload,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  return {
    documents: data?.documents ?? [],
    isLoading,
    error,
    uploadDocument: uploadMutation.mutate,
    isUploading: uploadMutation.isPending,
  };
};
```

### 3. Create an API Service

```typescript
// src/services/documents.service.ts

import { apiClient } from '@/lib/axios';
import { Document, SearchQuery, SearchResponse } from '@/types';

export const documentsService = {
  async getAll() {
    const { data } = await apiClient.get<{ documents: Document[] }>(
      '/documents'
    );
    return data;
  },

  async getById(id: string) {
    const { data } = await apiClient.get<Document>(`/documents/${id}`);
    return data;
  },

  async upload(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await apiClient.post<Document>('/documents/upload', formData);
    return data;
  },

  async search(query: SearchQuery) {
    const { data } = await apiClient.post<SearchResponse>('/search', query);
    return data;
  },

  async delete(id: string) {
    await apiClient.delete(`/documents/${id}`);
  },
};
```

### 4. Create a Zustand Store

```typescript
// src/store/useUIStore.ts

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  viewMode: 'timeline' | 'grid' | 'list';
  
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  setViewMode: (mode: 'timeline' | 'grid' | 'list') => void;
}

export const useUIStore = create<UIState>()(
  devtools((set) => ({
    sidebarOpen: true,
    theme: 'dark',
    viewMode: 'timeline',

    toggleSidebar: () =>
      set((state) => ({ sidebarOpen: !state.sidebarOpen })),

    setTheme: (theme) => set({ theme }),

    setViewMode: (mode) => set({ viewMode: mode }),
  }))
);
```

## Styling Guidelines

### Using Tailwind

```tsx
// Good - Use Tailwind utilities
<div className="flex items-center gap-4 p-6 bg-bg-tertiary rounded-lg">
  <h2 className="text-2xl font-bold text-text-primary">Title</h2>
  <button className="px-4 py-2 bg-accent-primary hover:bg-accent-primary/90 rounded">
    Click me
  </button>
</div>

// Avoid - Writing custom CSS unless necessary
```

### Custom Animations with Framer Motion

```tsx
import { motion } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, scale: 0.9 }}
  animate={{ opacity: 1, scale: 1 }}
  exit={{ opacity: 0, scale: 0.9 }}
  transition={{ duration: 0.2 }}
>
  Content
</motion.div>
```

### Using CSS Variables

```css
/* src/styles/globals.css */
:root {
  --bg-primary: #0F1419;
  --text-primary: #E8EAED;
}

/* Use in components */
.custom-element {
  background: var(--bg-primary);
  color: var(--text-primary);
}
```

## Data Fetching Patterns

### Simple Query

```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['document', id],
  queryFn: () => documentsService.getById(id),
});
```

### Infinite Query (Timeline)

```typescript
const {
  data,
  fetchNextPage,
  hasNextPage,
  isFetchingNextPage,
} = useInfiniteQuery({
  queryKey: ['documents', 'timeline'],
  queryFn: ({ pageParam = 0 }) =>
    documentsService.getTimeline({ page: pageParam }),
  getNextPageParam: (lastPage) => lastPage.nextPage,
});
```

### Mutation with Optimistic Updates

```typescript
const updateMutation = useMutation({
  mutationFn: documentsService.update,
  onMutate: async (newDoc) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['documents'] });
    
    // Snapshot previous value
    const previous = queryClient.getQueryData(['documents']);
    
    // Optimistically update
    queryClient.setQueryData(['documents'], (old) => {
      return old.map((doc) => (doc.id === newDoc.id ? newDoc : doc));
    });
    
    return { previous };
  },
  onError: (err, newDoc, context) => {
    // Rollback on error
    queryClient.setQueryData(['documents'], context.previous);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['documents'] });
  },
});
```

## OAuth Integration

### Google OAuth Setup

```typescript
// src/lib/oauth.ts

import { GoogleOAuthProvider } from '@react-oauth/google';

// In App.tsx
<GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
  <App />
</GoogleOAuthProvider>
```

### Using Google Login

```typescript
// src/features/auth/components/GoogleConnect.tsx

import { useGoogleLogin } from '@react-oauth/google';

export const GoogleConnect = () => {
  const login = useGoogleLogin({
    onSuccess: async (codeResponse) => {
      // Send code to backend
      await connectionsService.connectGoogle(codeResponse.code);
    },
    scope: 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/drive.readonly',
    flow: 'auth-code',
  });

  return (
    <button onClick={() => login()}>
      Connect Gmail & Drive
    </button>
  );
};
```

## Testing

### Unit Tests with Vitest

```typescript
// src/components/DocumentCard.test.tsx

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentCard } from './DocumentCard';

describe('DocumentCard', () => {
  it('renders document information', () => {
    const doc = {
      id: '1',
      filename: 'test.pdf',
      summary: 'Test summary',
    };

    render(<DocumentCard document={doc} />);

    expect(screen.getByText('test.pdf')).toBeInTheDocument();
    expect(screen.getByText('Test summary')).toBeInTheDocument();
  });

  it('calls onView when view button clicked', () => {
    const onView = vi.fn();
    const doc = { id: '1', filename: 'test.pdf' };

    render(<DocumentCard document={doc} onView={onView} />);

    fireEvent.click(screen.getByLabelText('View document'));
    expect(onView).toHaveBeenCalledWith(doc);
  });
});
```

### E2E Tests with Playwright

```typescript
// tests/e2e/timeline.spec.ts

import { test, expect } from '@playwright/test';

test('timeline displays documents', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Wait for timeline to load
  await page.waitForSelector('.timeline-view');

  // Check for document cards
  const cards = await page.locator('.document-card').count();
  expect(cards).toBeGreaterThan(0);
});

test('can search for documents', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Type in search
  await page.fill('input[type="search"]', 'meeting notes');
  await page.press('input[type="search"]', 'Enter');

  // Check results
  await expect(page.locator('.search-results')).toBeVisible();
});
```

## Performance Optimization

### Code Splitting

```typescript
// Lazy load pages
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Search = lazy(() => import('@/pages/Search'));

// In App.tsx
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/" element={<Dashboard />} />
    <Route path="/search" element={<Search />} />
  </Routes>
</Suspense>
```

### Virtualization for Long Lists

```typescript
import { Virtuoso } from 'react-virtuoso';

<Virtuoso
  data={documents}
  itemContent={(index, doc) => <DocumentCard document={doc} />}
  endReached={loadMore}
/>
```

### Memoization

```typescript
import { useMemo, memo } from 'react';

// Memoize expensive computations
const sortedDocs = useMemo(
  () => documents.sort((a, b) => b.uploadDate - a.uploadDate),
  [documents]
);

// Memoize components
export const DocumentCard = memo(({ document }) => {
  // Component code
});
```

## Build & Deployment

### Development Build

```bash
npm run dev
```

### Production Build

```bash
npm run build
# Output in ./dist
```

### Preview Production Build

```bash
npm run preview
```

### Docker Build

```dockerfile
# Dockerfile.frontend

FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Environment-Specific Builds

```bash
# Development
npm run build -- --mode development

# Production
npm run build -- --mode production
```

## Common Patterns

### Loading States

```tsx
if (isLoading) return <Skeleton />;
if (error) return <ErrorMessage error={error} />;
if (!data) return <EmptyState />;

return <Content data={data} />;
```

### Error Boundaries

```tsx
import { ErrorBoundary } from 'react-error-boundary';

<ErrorBoundary
  FallbackComponent={ErrorFallback}
  onReset={() => window.location.reload()}
>
  <App />
</ErrorBoundary>
```

### Toast Notifications

```tsx
import { useToast } from '@/hooks/useToast';

const { toast } = useToast();

toast({
  title: 'Success',
  description: 'Document uploaded',
  variant: 'success',
});
```

## Troubleshooting

### Common Issues

**API CORS errors**
```typescript
// Make sure backend allows origin: http://localhost:3000
// Or use proxy in vite.config.ts
```

**OAuth not working**
```bash
# Check environment variables are set
echo $VITE_GOOGLE_CLIENT_ID

# Make sure redirect URI matches in Google Console
```

**Slow builds**
```bash
# Clear cache
rm -rf node_modules/.vite

# Restart dev server
npm run dev
```

## Next Steps

1. Start backend API server
2. Set up OAuth credentials
3. Run `npm install && npm run dev`
4. Begin building components from UI spec
5. Integrate with backend API endpoints
