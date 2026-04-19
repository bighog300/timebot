# Frontend Application - Technical Specification

## Technology Stack

### Core Framework
- **React 18.3** - UI framework with concurrent features
- **TypeScript 5.4** - Type safety
- **Vite 5.2** - Build tool and dev server
- **React Router 6.22** - Client-side routing

### State Management
- **Zustand 4.5** - Lightweight state management
- **TanStack Query 5.28** - Server state & caching
- **Immer 10.0** - Immutable state updates

### UI & Styling
- **Tailwind CSS 3.4** - Utility-first CSS
- **Framer Motion 11.0** - Animation library
- **Radix UI** - Headless component primitives
- **Lucide React** - Icon library
- **React Virtuoso** - Virtual scrolling for timeline

### Data Visualization
- **Recharts 2.12** - Charts and graphs
- **D3.js 7.9** - Custom visualizations

### Form & Validation
- **React Hook Form 7.51** - Form management
- **Zod 3.22** - Schema validation

### API & Authentication
- **Axios 1.6** - HTTP client
- **OAuth libraries** - Google, Dropbox auth

### Development Tools
- **ESLint** - Linting
- **Prettier** - Code formatting
- **Vitest** - Unit testing
- **Playwright** - E2E testing

## Project Structure

```
frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
│
├── src/
│   ├── main.tsx                    # App entry point
│   ├── App.tsx                     # Root component
│   ├── vite-env.d.ts              # Vite types
│   │
│   ├── assets/                     # Static assets
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   │
│   ├── components/                 # Reusable components
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── MainLayout.tsx
│   │   │   └── MobileNav.tsx
│   │   │
│   │   ├── document/
│   │   │   ├── DocumentCard.tsx
│   │   │   ├── DocumentGrid.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   ├── DocumentDetail.tsx
│   │   │   └── DocumentTimeline.tsx
│   │   │
│   │   ├── timeline/
│   │   │   ├── TimelineView.tsx
│   │   │   ├── TimelineScrubber.tsx
│   │   │   ├── TimelineCluster.tsx
│   │   │   └── TimelineMarker.tsx
│   │   │
│   │   ├── search/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── SearchResults.tsx
│   │   │   ├── SearchFilters.tsx
│   │   │   └── SearchSuggestions.tsx
│   │   │
│   │   ├── connections/
│   │   │   ├── ConnectionCard.tsx
│   │   │   ├── ConnectionsList.tsx
│   │   │   ├── ConnectionSetup.tsx
│   │   │   └── SyncStatus.tsx
│   │   │
│   │   ├── categories/
│   │   │   ├── CategoryBadge.tsx
│   │   │   ├── CategoryList.tsx
│   │   │   ├── CategoryManager.tsx
│   │   │   └── CategoryStats.tsx
│   │   │
│   │   ├── insights/
│   │   │   ├── InsightCard.tsx
│   │   │   ├── TrendChart.tsx
│   │   │   ├── ActionItems.tsx
│   │   │   └── RelatedDocs.tsx
│   │   │
│   │   └── ui/                     # Base UI components
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Card.tsx
│   │       ├── Badge.tsx
│   │       ├── Modal.tsx
│   │       ├── Dropdown.tsx
│   │       ├── Tabs.tsx
│   │       ├── Tooltip.tsx
│   │       ├── Progress.tsx
│   │       ├── Skeleton.tsx
│   │       └── Toast.tsx
│   │
│   ├── pages/                      # Page components
│   │   ├── Dashboard.tsx           # Main timeline view
│   │   ├── Search.tsx              # Search results page
│   │   ├── Categories.tsx          # Category explorer
│   │   ├── Connections.tsx         # Cloud connections manager
│   │   ├── Insights.tsx            # Insights dashboard
│   │   ├── Settings.tsx            # User settings
│   │   └── NotFound.tsx            # 404 page
│   │
│   ├── features/                   # Feature modules
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   └── services/
│   │   │
│   │   ├── documents/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   └── types.ts
│   │   │
│   │   └── timeline/
│   │       ├── components/
│   │       ├── hooks/
│   │       ├── utils/
│   │       └── types.ts
│   │
│   ├── hooks/                      # Custom React hooks
│   │   ├── useDocuments.ts
│   │   ├── useSearch.ts
│   │   ├── useCategories.ts
│   │   ├── useConnections.ts
│   │   ├── useTimeline.ts
│   │   ├── useInfiniteScroll.ts
│   │   ├── useDebounce.ts
│   │   └── useLocalStorage.ts
│   │
│   ├── services/                   # API services
│   │   ├── api.ts                  # Axios instance
│   │   ├── documents.service.ts
│   │   ├── categories.service.ts
│   │   ├── search.service.ts
│   │   ├── connections.service.ts
│   │   ├── auth.service.ts
│   │   └── insights.service.ts
│   │
│   ├── store/                      # Zustand stores
│   │   ├── index.ts
│   │   ├── useDocumentStore.ts
│   │   ├── useCategoryStore.ts
│   │   ├── useUIStore.ts
│   │   ├── useAuthStore.ts
│   │   └── useConnectionStore.ts
│   │
│   ├── types/                      # TypeScript types
│   │   ├── document.types.ts
│   │   ├── category.types.ts
│   │   ├── connection.types.ts
│   │   ├── search.types.ts
│   │   └── api.types.ts
│   │
│   ├── utils/                      # Utility functions
│   │   ├── format.ts               # Date, number formatting
│   │   ├── validation.ts           # Form validation
│   │   ├── storage.ts              # LocalStorage helpers
│   │   ├── api.ts                  # API helpers
│   │   └── constants.ts            # App constants
│   │
│   ├── styles/                     # Global styles
│   │   ├── globals.css             # Global CSS + Tailwind
│   │   ├── animations.css          # Animation keyframes
│   │   └── themes.css              # Theme variables
│   │
│   └── lib/                        # Third-party configs
│       ├── queryClient.ts          # TanStack Query config
│       ├── axios.ts                # Axios config
│       └── oauth.ts                # OAuth configs
│
├── .env.example                    # Environment template
├── .env.development                # Dev environment
├── .env.production                 # Prod environment
├── .eslintrc.cjs                   # ESLint config
├── .prettierrc                     # Prettier config
├── tsconfig.json                   # TypeScript config
├── tailwind.config.js              # Tailwind config
├── vite.config.ts                  # Vite config
├── package.json                    # Dependencies
└── README.md                       # Frontend docs
```

## Key TypeScript Types

### Document Types

```typescript
// src/types/document.types.ts

export interface Document {
  id: string;
  filename: string;
  originalPath: string;
  fileType: string;
  fileSize: number;
  mimeType: string;
  
  // Timestamps
  uploadDate: string;
  lastModified: string;
  processedDate?: string;
  
  // Content
  rawText?: string;
  pageCount?: number;
  wordCount?: number;
  
  // AI Analysis
  summary?: string;
  keyPoints?: string[];
  entities?: DocumentEntities;
  actionItems?: ActionItem[];
  
  // Categorization
  aiCategory?: Category;
  aiCategoryId?: string;
  aiConfidence?: number;
  userCategory?: Category;
  userCategoryId?: string;
  
  // Tags
  aiTags: string[];
  userTags: string[];
  
  // Metadata
  extractedMetadata?: Record<string, any>;
  processingStatus: ProcessingStatus;
  processingError?: string;
  
  // User flags
  isFavorite: boolean;
  isArchived: boolean;
  userNotes?: string;
  
  // Source
  source: DocumentSource;
  sourceId?: string;
  
  // Related
  relatedDocuments?: RelatedDocument[];
}

export interface DocumentEntities {
  people: string[];
  organizations: string[];
  dates: string[];
  locations: string[];
}

export interface ActionItem {
  id: string;
  text: string;
  assignee?: string;
  dueDate?: string;
  completed: boolean;
}

export interface RelatedDocument {
  id: string;
  filename: string;
  relationshipType: 'similar_to' | 'references' | 'follows_up' | 'related_to';
  confidence: number;
}

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type DocumentSource = 'upload' | 'gmail' | 'gdrive' | 'dropbox' | 'onedrive';

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  color: string;
  icon?: string;
  aiGenerated: boolean;
  documentCount: number;
  createdAt: string;
  updatedAt: string;
}
```

### Connection Types

```typescript
// src/types/connection.types.ts

export interface Connection {
  id: string;
  type: ConnectionType;
  status: ConnectionStatus;
  displayName: string;
  email?: string;
  
  // Sync info
  lastSyncDate?: string;
  lastSyncStatus?: SyncStatus;
  syncProgress?: number;
  
  // Stats
  documentCount: number;
  totalSize: number;
  
  // Settings
  autoSync: boolean;
  syncInterval: number; // minutes
  
  // Credentials (encrypted on backend)
  isAuthenticated: boolean;
  expiresAt?: string;
  
  createdAt: string;
  updatedAt: string;
}

export type ConnectionType = 'gmail' | 'gdrive' | 'dropbox' | 'onedrive';

export type ConnectionStatus = 'connected' | 'disconnected' | 'error' | 'syncing';

export type SyncStatus = 'success' | 'failed' | 'partial' | 'in_progress';

export interface SyncLog {
  id: string;
  connectionId: string;
  startTime: string;
  endTime?: string;
  status: SyncStatus;
  documentsAdded: number;
  documentsUpdated: number;
  documentsFailed: number;
  errorMessage?: string;
}
```

### Search Types

```typescript
// src/types/search.types.ts

export interface SearchQuery {
  query: string;
  filters?: SearchFilters;
  page?: number;
  limit?: number;
}

export interface SearchFilters {
  categories?: string[];
  sources?: DocumentSource[];
  dateRange?: DateRange;
  fileTypes?: string[];
  tags?: string[];
  isFavorite?: boolean;
  isArchived?: boolean;
}

export interface DateRange {
  start?: string;
  end?: string;
}

export interface SearchResult {
  document: Document;
  relevance: number;
  highlights?: SearchHighlight[];
}

export interface SearchHighlight {
  field: string;
  snippet: string;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  totalPages: number;
  aiUnderstanding?: string;
}
```

## Component Examples

### Document Card Component

```typescript
// src/components/document/DocumentCard.tsx

import { motion } from 'framer-motion';
import { FileText, Star, Link2, Eye } from 'lucide-react';
import { Document } from '@/types/document.types';
import { CategoryBadge } from '@/components/categories/CategoryBadge';
import { formatDate, formatFileSize } from '@/utils/format';

interface DocumentCardProps {
  document: Document;
  onView?: (doc: Document) => void;
  onToggleFavorite?: (doc: Document) => void;
  onViewRelated?: (doc: Document) => void;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  document,
  onView,
  onToggleFavorite,
  onViewRelated,
}) => {
  return (
    <motion.div
      className="document-card group"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      transition={{ duration: 0.2 }}
    >
      <div className="card-header">
        <FileText className="document-icon" size={20} />
        {document.aiCategory && (
          <CategoryBadge category={document.aiCategory} />
        )}
      </div>

      <h3 className="document-title" title={document.filename}>
        {document.filename}
      </h3>

      {document.summary && (
        <p className="document-summary">{document.summary}</p>
      )}

      <div className="card-meta">
        <span className="meta-date">
          {formatDate(document.uploadDate)}
        </span>
        <span className="meta-source">{document.source}</span>
        <span className="meta-size">
          {formatFileSize(document.fileSize)}
        </span>
      </div>

      {document.aiTags.length > 0 && (
        <div className="card-tags">
          {document.aiTags.slice(0, 3).map((tag) => (
            <span key={tag} className="tag">
              {tag}
            </span>
          ))}
          {document.aiTags.length > 3 && (
            <span className="tag-more">+{document.aiTags.length - 3}</span>
          )}
        </div>
      )}

      <div className="card-actions">
        <button
          className="btn-icon"
          onClick={() => onView?.(document)}
          aria-label="View document"
        >
          <Eye size={16} />
        </button>
        
        <button
          className={`btn-icon ${document.isFavorite ? 'active' : ''}`}
          onClick={() => onToggleFavorite?.(document)}
          aria-label="Toggle favorite"
        >
          <Star size={16} fill={document.isFavorite ? 'currentColor' : 'none'} />
        </button>
        
        {document.relatedDocuments && document.relatedDocuments.length > 0 && (
          <button
            className="btn-icon"
            onClick={() => onViewRelated?.(document)}
            aria-label="View related documents"
          >
            <Link2 size={16} />
          </button>
        )}
      </div>
    </motion.div>
  );
};
```

### Timeline View Component

```typescript
// src/components/timeline/TimelineView.tsx

import { useState, useCallback } from 'react';
import { Virtuoso } from 'react-virtuoso';
import { useInfiniteQuery } from '@tanstack/react-query';
import { documentsService } from '@/services/documents.service';
import { DocumentCard } from '@/components/document/DocumentCard';
import { TimelineScrubber } from './TimelineScrubber';
import { TimelineCluster } from './TimelineCluster';
import { groupDocumentsByDate } from '@/utils/timeline';

export const TimelineView: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['documents', 'timeline'],
    queryFn: ({ pageParam = 0 }) =>
      documentsService.getTimeline({ page: pageParam, limit: 50 }),
    getNextPageParam: (lastPage) => lastPage.nextPage,
  });

  const documents = data?.pages.flatMap((page) => page.documents) ?? [];
  const clusteredDocs = groupDocumentsByDate(documents);

  const loadMore = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  return (
    <div className="timeline-view">
      <TimelineScrubber
        documents={documents}
        selectedDate={selectedDate}
        onDateChange={setSelectedDate}
      />

      <Virtuoso
        data={clusteredDocs}
        endReached={loadMore}
        itemContent={(index, cluster) => (
          <TimelineCluster
            key={cluster.date}
            date={cluster.date}
            documents={cluster.documents}
          />
        )}
        components={{
          Footer: () =>
            isFetchingNextPage ? (
              <div className="timeline-loader">Loading more...</div>
            ) : null,
        }}
      />
    </div>
  );
};
```

### Connection Card Component

```typescript
// src/components/connections/ConnectionCard.tsx

import { motion } from 'framer-motion';
import { RefreshCw, Settings, Trash2 } from 'lucide-react';
import { Connection } from '@/types/connection.types';
import { formatDate, formatNumber } from '@/utils/format';

interface ConnectionCardProps {
  connection: Connection;
  onSync?: (conn: Connection) => void;
  onSettings?: (conn: Connection) => void;
  onDisconnect?: (conn: Connection) => void;
}

export const ConnectionCard: React.FC<ConnectionCardProps> = ({
  connection,
  onSync,
  onSettings,
  onDisconnect,
}) => {
  const statusColors = {
    connected: 'bg-green-500',
    syncing: 'bg-blue-500',
    error: 'bg-red-500',
    disconnected: 'bg-gray-500',
  };

  const iconMap = {
    gmail: '📧',
    gdrive: '📁',
    dropbox: '📦',
    onedrive: '☁️',
  };

  return (
    <motion.div
      className="connection-card"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
    >
      <div className="connection-header">
        <div className="service-info">
          <span className="service-icon">{iconMap[connection.type]}</span>
          <div>
            <h4>{connection.displayName}</h4>
            {connection.email && (
              <p className="service-email">{connection.email}</p>
            )}
          </div>
        </div>
        
        <div className={`status-indicator ${statusColors[connection.status]}`} />
      </div>

      {connection.status === 'syncing' && connection.syncProgress && (
        <div className="progress-bar">
          <motion.div
            className="progress-fill"
            initial={{ width: 0 }}
            animate={{ width: `${connection.syncProgress}%` }}
          />
        </div>
      )}

      <div className="connection-stats">
        <div className="stat">
          <span className="stat-label">Last sync</span>
          <span className="stat-value">
            {connection.lastSyncDate
              ? formatDate(connection.lastSyncDate)
              : 'Never'}
          </span>
        </div>
        
        <div className="stat">
          <span className="stat-label">Documents</span>
          <span className="stat-value">
            {formatNumber(connection.documentCount)}
          </span>
        </div>
      </div>

      <div className="connection-actions">
        <button
          className="btn-icon"
          onClick={() => onSync?.(connection)}
          disabled={connection.status === 'syncing'}
          aria-label="Sync now"
        >
          <RefreshCw
            size={16}
            className={connection.status === 'syncing' ? 'animate-spin' : ''}
          />
        </button>
        
        <button
          className="btn-icon"
          onClick={() => onSettings?.(connection)}
          aria-label="Settings"
        >
          <Settings size={16} />
        </button>
        
        <button
          className="btn-icon btn-danger"
          onClick={() => onDisconnect?.(connection)}
          aria-label="Disconnect"
        >
          <Trash2 size={16} />
        </button>
      </div>
    </motion.div>
  );
};
```

## State Management with Zustand

```typescript
// src/store/useDocumentStore.ts

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { Document } from '@/types/document.types';

interface DocumentState {
  documents: Document[];
  selectedDocument: Document | null;
  viewMode: 'timeline' | 'grid' | 'list';
  
  setDocuments: (docs: Document[]) => void;
  addDocument: (doc: Document) => void;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  removeDocument: (id: string) => void;
  selectDocument: (doc: Document | null) => void;
  setViewMode: (mode: 'timeline' | 'grid' | 'list') => void;
  toggleFavorite: (id: string) => void;
}

export const useDocumentStore = create<DocumentState>()(
  devtools(
    persist(
      immer((set) => ({
        documents: [],
        selectedDocument: null,
        viewMode: 'timeline',

        setDocuments: (docs) =>
          set((state) => {
            state.documents = docs;
          }),

        addDocument: (doc) =>
          set((state) => {
            state.documents.unshift(doc);
          }),

        updateDocument: (id, updates) =>
          set((state) => {
            const index = state.documents.findIndex((d) => d.id === id);
            if (index !== -1) {
              state.documents[index] = {
                ...state.documents[index],
                ...updates,
              };
            }
          }),

        removeDocument: (id) =>
          set((state) => {
            state.documents = state.documents.filter((d) => d.id !== id);
          }),

        selectDocument: (doc) =>
          set((state) => {
            state.selectedDocument = doc;
          }),

        setViewMode: (mode) =>
          set((state) => {
            state.viewMode = mode;
          }),

        toggleFavorite: (id) =>
          set((state) => {
            const doc = state.documents.find((d) => d.id === id);
            if (doc) {
              doc.isFavorite = !doc.isFavorite;
            }
          }),
      })),
      {
        name: 'document-store',
        partialize: (state) => ({
          viewMode: state.viewMode,
        }),
      }
    )
  )
);
```

## Next Documents Needed

1. **Tailwind Configuration** - Complete theme setup
2. **API Service Layer** - All API endpoints implementation
3. **React Router Configuration** - Route structure
4. **OAuth Integration** - Gmail, Drive, Dropbox auth flows
5. **Testing Setup** - Unit and E2E test configuration
6. **Build & Deployment** - Docker setup for frontend
7. **Storybook Configuration** - Component documentation
