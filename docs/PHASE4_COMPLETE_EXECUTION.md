# PHASE 4: FRONTEND - COMPLETE EXECUTION PROMPT

## OVERVIEW FOR AI CODING ASSISTANT

You are building the complete frontend UI for the Document Intelligence Platform. After Phases 1-3, you have a powerful backend with AI processing, cloud sync, and advanced search. Now you'll create a beautiful, responsive React interface to visualize and interact with all this intelligence.

This prompt covers **the complete frontend** (8 weeks of work). The frontend is substantial, so we'll build it in logical feature groups.

---

## PREREQUISITES

✅ **Backend must be complete (Phases 1-3):**
- API endpoints working
- Documents being processed
- Search functional
- Insights generating

✅ **Design specifications available:**
- UI_DESIGN_SPEC.md (design system)
- FRONTEND_TECH_SPEC.md (architecture)
- FRONTEND_DEV_GUIDE.md (development guide)

---

## PROJECT SETUP

### 1. Initialize React Project

```bash
# Create frontend directory
cd doc-intelligence-platform
npx create-vite@latest frontend -- --template react-ts

cd frontend

# Install core dependencies
npm install react-router-dom@6.22.0 \
  @tanstack/react-query@5.17.0 \
  zustand@4.5.0 \
  axios@1.6.5 \
  date-fns@3.3.1

# Install UI components
npm install @radix-ui/react-dialog@1.0.5 \
  @radix-ui/react-dropdown-menu@2.0.6 \
  @radix-ui/react-select@2.0.0 \
  @radix-ui/react-tabs@1.0.4 \
  @radix-ui/react-tooltip@1.0.7 \
  @radix-ui/react-scroll-area@1.0.5 \
  lucide-react@0.323.0

# Install styling
npm install tailwindcss@3.4.1 \
  postcss@8.4.33 \
  autoprefixer@10.4.17 \
  clsx@2.1.0 \
  tailwind-merge@2.2.1

# Install visualization
npm install recharts@2.10.4 \
  d3@7.8.5 \
  framer-motion@11.0.3

# Install utilities
npm install react-virtuoso@4.6.2 \
  react-markdown@9.0.1 \
  socket.io-client@4.6.1
```

### 2. Configure Tailwind CSS

```javascript
// tailwind.config.js

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Information Cartography theme
        dark: {
          50: '#E8EAED',
          100: '#C4C9D1',
          200: '#A0A8B5',
          300: '#7C8799',
          400: '#58667D',
          500: '#344561',
          600: '#2A3751',
          700: '#202941',
          800: '#161B31',
          900: '#0F1419',
        },
        accent: {
          blue: '#3B82F6',
          purple: '#8B5CF6',
          green: '#10B981',
          yellow: '#F59E0B',
          red: '#EF4444',
        }
      },
      fontFamily: {
        display: ['"Space Mono"', 'monospace'],
        body: ['Inter', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-in',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
```

```css
/* src/index.css */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-dark-700;
  }
  
  body {
    @apply bg-dark-900 text-dark-50 font-body antialiased;
  }
  
  h1, h2, h3, h4, h5, h6 {
    @apply font-display;
  }
}

@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-accent-blue text-white rounded-lg font-medium 
           hover:bg-blue-600 transition-colors duration-200
           focus:outline-none focus:ring-2 focus:ring-accent-blue/50;
  }
  
  .btn-secondary {
    @apply px-4 py-2 bg-dark-800 text-dark-100 rounded-lg font-medium
           hover:bg-dark-700 transition-colors duration-200
           focus:outline-none focus:ring-2 focus:ring-dark-600;
  }
  
  .input-field {
    @apply w-full px-4 py-2 bg-dark-800 border border-dark-700 rounded-lg
           text-dark-50 placeholder-dark-400
           focus:outline-none focus:ring-2 focus:ring-accent-blue/50
           transition-all duration-200;
  }
  
  .card {
    @apply bg-dark-800 rounded-xl border border-dark-700 p-6
           hover:border-dark-600 transition-all duration-200;
  }
}
```

### 3. Project Structure

```
frontend/
├── src/
│   ├── api/                    # API client
│   │   ├── client.ts
│   │   ├── documents.ts
│   │   ├── search.ts
│   │   ├── connections.ts
│   │   └── insights.ts
│   │
│   ├── components/            # Reusable components
│   │   ├── ui/               # Base UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Dialog.tsx
│   │   │   └── Tooltip.tsx
│   │   │
│   │   ├── documents/        # Document components
│   │   │   ├── DocumentCard.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   ├── DocumentDetail.tsx
│   │   │   └── DocumentUpload.tsx
│   │   │
│   │   ├── search/           # Search components
│   │   │   ├── SearchBar.tsx
│   │   │   ├── SearchFilters.tsx
│   │   │   ├── SearchResults.tsx
│   │   │   └── SearchSuggestions.tsx
│   │   │
│   │   ├── timeline/         # Timeline components
│   │   │   ├── Timeline.tsx
│   │   │   ├── TimelineItem.tsx
│   │   │   └── TimelineScrubber.tsx
│   │   │
│   │   ├── connections/      # Connection components
│   │   │   ├── ConnectionCard.tsx
│   │   │   ├── ConnectionStatus.tsx
│   │   │   └── OAuthButton.tsx
│   │   │
│   │   └── insights/         # Insights components
│   │       ├── DailyInsights.tsx
│   │       ├── TrendChart.tsx
│   │       └── ActionItems.tsx
│   │
│   ├── views/                # Page views
│   │   ├── HomePage.tsx
│   │   ├── TimelineView.tsx
│   │   ├── SearchView.tsx
│   │   ├── DocumentView.tsx
│   │   ├── ConnectionsView.tsx
│   │   ├── InsightsView.tsx
│   │   └── SettingsView.tsx
│   │
│   ├── store/                # State management
│   │   ├── useDocumentStore.ts
│   │   ├── useSearchStore.ts
│   │   ├── useConnectionStore.ts
│   │   └── useUIStore.ts
│   │
│   ├── hooks/                # Custom hooks
│   │   ├── useDocuments.ts
│   │   ├── useSearch.ts
│   │   ├── useWebSocket.ts
│   │   └── useInfiniteScroll.ts
│   │
│   ├── utils/                # Utility functions
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── cn.ts
│   │
│   ├── types/                # TypeScript types
│   │   ├── document.ts
│   │   ├── search.ts
│   │   └── api.ts
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
│
├── public/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## PART 1: CORE INFRASTRUCTURE (WEEK 25-26)

### Task 1: API Client Setup

```typescript
// src/api/client.ts

import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get<T>(url, { params });
    return response.data;
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(url, data);
    return response.data;
  }

  async put<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(url, data);
    return response.data;
  }

  async delete<T>(url: string): Promise<T> {
    const response = await this.client.delete<T>(url);
    return response.data;
  }

  async upload<T>(url: string, formData: FormData, onProgress?: (progress: number) => void): Promise<T> {
    const response = await this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });
    return response.data;
  }
}

export const apiClient = new APIClient();
```

```typescript
// src/api/documents.ts

import { apiClient } from './client';
import type { Document, DocumentCreate, DocumentUpdate } from '../types/document';

export const documentsAPI = {
  // List documents
  list: (params?: {
    skip?: number;
    limit?: number;
    source?: string;
    category_id?: string;
  }) => {
    return apiClient.get<{ results: Document[]; total: number }>('/documents', params);
  },

  // Get document by ID
  get: (id: string) => {
    return apiClient.get<Document>(`/documents/${id}`);
  },

  // Upload document
  upload: (file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.upload<Document>('/upload', formData, onProgress);
  },

  // Update document
  update: (id: string, data: DocumentUpdate) => {
    return apiClient.put<Document>(`/documents/${id}`, data);
  },

  // Delete document
  delete: (id: string) => {
    return apiClient.delete(`/documents/${id}`);
  },

  // Get similar documents
  similar: (id: string, limit?: number) => {
    return apiClient.get<{ similar_documents: Document[] }>(
      `/search/documents/${id}/similar`,
      { limit }
    );
  },
};
```

```typescript
// src/api/search.ts

import { apiClient } from './client';
import type { SearchResult } from '../types/search';

export const searchAPI = {
  // Keyword search
  search: (params: {
    query: string;
    categories?: string[];
    sources?: string[];
    tags?: string[];
    date_start?: string;
    date_end?: string;
    skip?: number;
    limit?: number;
  }) => {
    return apiClient.post<SearchResult>('/search', null, { params });
  },

  // Semantic search
  semanticSearch: (params: {
    query: string;
    limit?: number;
    threshold?: number;
  }) => {
    return apiClient.post<SearchResult>('/search/semantic', null, { params });
  },

  // Get suggestions
  suggestions: (query: string) => {
    return apiClient.get<{ suggestions: string[] }>(
      '/search/suggestions',
      { q: query }
    );
  },

  // Get facets
  facets: (query?: string) => {
    return apiClient.get('/search/facets', { query });
  },
};
```

### Task 2: TypeScript Types

```typescript
// src/types/document.ts

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  mime_type: string;
  upload_date: string;
  processing_status: 'queued' | 'processing' | 'completed' | 'failed';
  
  // AI Analysis
  summary?: string;
  key_points?: string[];
  entities?: {
    people?: string[];
    organizations?: string[];
    dates?: string[];
    locations?: string[];
  };
  action_items?: ActionItem[];
  
  // Categorization
  ai_category?: Category;
  ai_tags?: string[];
  ai_confidence?: number;
  
  // User fields
  user_category?: Category;
  user_tags?: string[];
  user_notes?: string;
  is_favorite: boolean;
  is_archived: boolean;
  
  // Source
  source: 'upload' | 'gmail' | 'gdrive' | 'dropbox';
  source_id?: string;
  connection_id?: string;
  
  // Metadata
  raw_text?: string;
  page_count?: number;
  word_count?: number;
  extracted_metadata?: Record<string, any>;
}

export interface ActionItem {
  text: string;
  assignee?: string;
  due_date?: string;
  priority: 'low' | 'medium' | 'high';
  completed?: boolean;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;
  color: string;
  icon?: string;
  document_count: number;
}

export interface DocumentCreate {
  file: File;
}

export interface DocumentUpdate {
  user_category_id?: string;
  user_tags?: string[];
  user_notes?: string;
  is_favorite?: boolean;
  is_archived?: boolean;
}
```

```typescript
// src/types/search.ts

export interface SearchFilters {
  categories?: string[];
  sources?: string[];
  tags?: string[];
  file_types?: string[];
  date_range?: {
    start?: string;
    end?: string;
  };
  is_favorite?: boolean;
}

export interface SearchResultItem {
  document: Document;
  relevance?: number;
  similarity_score?: number;
  highlights?: string[];
}

export interface SearchResult {
  results: SearchResultItem[];
  total: number;
  query: string;
  filters?: SearchFilters;
  page: number;
  pages: number;
}
```

### Task 3: State Management with Zustand

```typescript
// src/store/useDocumentStore.ts

import { create } from 'zustand';
import { Document } from '../types/document';

interface DocumentStore {
  documents: Document[];
  selectedDocument: Document | null;
  isLoading: boolean;
  error: string | null;
  
  setDocuments: (documents: Document[]) => void;
  addDocument: (document: Document) => void;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  removeDocument: (id: string) => void;
  setSelectedDocument: (document: Document | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useDocumentStore = create<DocumentStore>((set) => ({
  documents: [],
  selectedDocument: null,
  isLoading: false,
  error: null,
  
  setDocuments: (documents) => set({ documents }),
  
  addDocument: (document) =>
    set((state) => ({ documents: [document, ...state.documents] })),
  
  updateDocument: (id, updates) =>
    set((state) => ({
      documents: state.documents.map((doc) =>
        doc.id === id ? { ...doc, ...updates } : doc
      ),
      selectedDocument:
        state.selectedDocument?.id === id
          ? { ...state.selectedDocument, ...updates }
          : state.selectedDocument,
    })),
  
  removeDocument: (id) =>
    set((state) => ({
      documents: state.documents.filter((doc) => doc.id !== id),
      selectedDocument:
        state.selectedDocument?.id === id ? null : state.selectedDocument,
    })),
  
  setSelectedDocument: (document) => set({ selectedDocument: document }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));
```

```typescript
// src/store/useSearchStore.ts

import { create } from 'zustand';
import { SearchFilters, SearchResult } from '../types/search';

interface SearchStore {
  query: string;
  filters: SearchFilters;
  results: SearchResult | null;
  isSearching: boolean;
  searchMode: 'keyword' | 'semantic';
  
  setQuery: (query: string) => void;
  setFilters: (filters: SearchFilters) => void;
  setResults: (results: SearchResult | null) => void;
  setSearching: (isSearching: boolean) => void;
  setSearchMode: (mode: 'keyword' | 'semantic') => void;
  clearSearch: () => void;
}

export const useSearchStore = create<SearchStore>((set) => ({
  query: '',
  filters: {},
  results: null,
  isSearching: false,
  searchMode: 'keyword',
  
  setQuery: (query) => set({ query }),
  setFilters: (filters) => set({ filters }),
  setResults: (results) => set({ results }),
  setSearching: (isSearching) => set({ isSearching }),
  setSearchMode: (mode) => set({ searchMode: mode }),
  clearSearch: () => set({ query: '', filters: {}, results: null }),
}));
```

### Task 4: React Query Hooks

```typescript
// src/hooks/useDocuments.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsAPI } from '../api/documents';
import { useDocumentStore } from '../store/useDocumentStore';
import type { DocumentUpdate } from '../types/document';

export function useDocuments(params?: any) {
  const setDocuments = useDocumentStore((state) => state.setDocuments);
  
  return useQuery({
    queryKey: ['documents', params],
    queryFn: async () => {
      const data = await documentsAPI.list(params);
      setDocuments(data.results);
      return data;
    },
  });
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: ['document', id],
    queryFn: () => documentsAPI.get(id),
    enabled: !!id,
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  const addDocument = useDocumentStore((state) => state.addDocument);
  
  return useMutation({
    mutationFn: ({ file, onProgress }: { file: File; onProgress?: (p: number) => void }) =>
      documentsAPI.upload(file, onProgress),
    onSuccess: (document) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      addDocument(document);
    },
  });
}

export function useUpdateDocument() {
  const queryClient = useQueryClient();
  const updateDocument = useDocumentStore((state) => state.updateDocument);
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DocumentUpdate }) =>
      documentsAPI.update(id, data),
    onSuccess: (document) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['document', document.id] });
      updateDocument(document.id, document);
    },
  });
}

export function useSimilarDocuments(id: string) {
  return useQuery({
    queryKey: ['similar-documents', id],
    queryFn: () => documentsAPI.similar(id),
    enabled: !!id,
  });
}
```

```typescript
// src/hooks/useSearch.ts

import { useQuery } from '@tanstack/react-query';
import { searchAPI } from '../api/search';
import { useSearchStore } from '../store/useSearchStore';

export function useSearch() {
  const { query, filters, searchMode } = useSearchStore();
  
  return useQuery({
    queryKey: ['search', query, filters, searchMode],
    queryFn: async () => {
      if (!query) return null;
      
      if (searchMode === 'semantic') {
        return searchAPI.semanticSearch({ query, limit: 50 });
      } else {
        return searchAPI.search({ query, ...filters, limit: 50 });
      }
    },
    enabled: !!query,
  });
}

export function useSearchSuggestions(query: string) {
  return useQuery({
    queryKey: ['search-suggestions', query],
    queryFn: () => searchAPI.suggestions(query),
    enabled: query.length >= 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useSearchFacets(query?: string) {
  return useQuery({
    queryKey: ['search-facets', query],
    queryFn: () => searchAPI.facets(query),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}
```

### Task 5: Utility Functions

```typescript
// src/utils/cn.ts

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

```typescript
// src/utils/formatters.ts

import { formatDistanceToNow, format } from 'date-fns';

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

export function formatDate(date: string | Date): string {
  return format(new Date(date), 'MMM dd, yyyy');
}

export function formatDateTime(date: string | Date): string {
  return format(new Date(date), 'MMM dd, yyyy HH:mm');
}

export function formatRelativeTime(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true });
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

export function highlightText(text: string, query: string): string {
  if (!query) return text;
  
  const regex = new RegExp(`(${query})`, 'gi');
  return text.replace(regex, '<mark class="bg-yellow-500/30">$1</mark>');
}
```

### Task 6: Base UI Components

```typescript
// src/components/ui/Button.tsx

import React from 'react';
import { cn } from '../../utils/cn';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  className,
  disabled,
  ...props
}: ButtonProps) {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'bg-accent-blue text-white hover:bg-blue-600 focus:ring-accent-blue/50',
    secondary: 'bg-dark-800 text-dark-100 hover:bg-dark-700 focus:ring-dark-600',
    ghost: 'text-dark-300 hover:bg-dark-800 focus:ring-dark-700',
    danger: 'bg-accent-red text-white hover:bg-red-600 focus:ring-accent-red/50',
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };
  
  return (
    <button
      className={cn(baseStyles, variants[variant], sizes[size], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      )}
      {children}
    </button>
  );
}
```

```typescript
// src/components/ui/Input.tsx

import React from 'react';
import { cn } from '../../utils/cn';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export function Input({
  label,
  error,
  icon,
  className,
  ...props
}: InputProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-dark-200 mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-400">
            {icon}
          </div>
        )}
        <input
          className={cn(
            'input-field',
            icon && 'pl-10',
            error && 'border-accent-red focus:ring-accent-red/50',
            className
          )}
          {...props}
        />
      </div>
      {error && (
        <p className="mt-1 text-sm text-accent-red">{error}</p>
      )}
    </div>
  );
}
```

```typescript
// src/components/ui/Card.tsx

import React from 'react';
import { cn } from '../../utils/cn';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

export function Card({ children, hover = true, className, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'card',
        hover && 'hover:shadow-lg hover:-translate-y-0.5',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
```

---

Due to length, I'll continue with Parts 2-4 (UI Components, Views, and Features) in a follow-up. Should I continue creating the complete Phase 4 prompt?

---

## PART 2: DOCUMENT COMPONENTS (WEEK 27)

### Task 7: Document Upload

```typescript
// src/components/documents/DocumentUpload.tsx

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X } from 'lucide-react';
import { useUploadDocument } from '../../hooks/useDocuments';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';

export function DocumentUpload() {
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const uploadMutation = useUploadDocument();

  const onDrop = useCallback((acceptedFiles: File[]) => {
    acceptedFiles.forEach((file) => {
      uploadMutation.mutate(
        {
          file,
          onProgress: (progress) => {
            setUploadProgress((prev) => ({ ...prev, [file.name]: progress }));
          },
        },
        {
          onSuccess: () => {
            setTimeout(() => {
              setUploadProgress((prev) => {
                const { [file.name]: _, ...rest } = prev;
                return rest;
              });
            }, 2000);
          },
        }
      );
    });
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'text/plain': ['.txt'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
  });

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all',
          isDragActive
            ? 'border-accent-blue bg-accent-blue/10'
            : 'border-dark-700 hover:border-dark-600 hover:bg-dark-800/50'
        )}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-4 text-dark-400" />
        {isDragActive ? (
          <p className="text-lg text-accent-blue">Drop files here...</p>
        ) : (
          <>
            <p className="text-lg text-dark-200 mb-2">
              Drag & drop files here, or click to select
            </p>
            <p className="text-sm text-dark-400">
              Supports PDF, DOCX, XLSX, PPTX, images (max 50MB)
            </p>
          </>
        )}
      </div>

      {/* Upload Progress */}
      {Object.keys(uploadProgress).length > 0 && (
        <div className="space-y-2">
          {Object.entries(uploadProgress).map(([filename, progress]) => (
            <div key={filename} className="card">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <File className="w-5 h-5 text-accent-blue" />
                  <span className="text-sm font-medium">{filename}</span>
                </div>
                <span className="text-sm text-dark-400">{progress}%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div
                  className="bg-accent-blue h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Task 8: Document Card

```typescript
// src/components/documents/DocumentCard.tsx

import React from 'react';
import { FileText, Star, Calendar, Tag, ExternalLink } from 'lucide-react';
import { Document } from '../../types/document';
import { formatRelativeTime, formatFileSize } from '../../utils/formatters';
import { cn } from '../../utils/cn';

interface DocumentCardProps {
  document: Document;
  onClick?: () => void;
  onFavorite?: () => void;
}

export function DocumentCard({ document, onClick, onFavorite }: DocumentCardProps) {
  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'gmail': return '📧';
      case 'gdrive': return '📁';
      case 'dropbox': return '📦';
      default: return '📄';
    }
  };

  return (
    <div
      className={cn(
        'card cursor-pointer group',
        document.is_favorite && 'ring-2 ring-accent-yellow'
      )}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2 flex-1">
          <span className="text-2xl">{getSourceIcon(document.source)}</span>
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-dark-50 truncate group-hover:text-accent-blue transition-colors">
              {document.filename}
            </h3>
            <p className="text-sm text-dark-400">{formatFileSize(document.file_size)}</p>
          </div>
        </div>
        
        <button
          onClick={(e) => {
            e.stopPropagation();
            onFavorite?.();
          }}
          className={cn(
            'p-2 rounded-lg transition-colors',
            document.is_favorite
              ? 'text-accent-yellow'
              : 'text-dark-500 hover:text-accent-yellow hover:bg-dark-700'
          )}
        >
          <Star className={cn('w-5 h-5', document.is_favorite && 'fill-current')} />
        </button>
      </div>

      {/* Summary */}
      {document.summary && (
        <p className="text-sm text-dark-300 mb-3 line-clamp-2">
          {document.summary}
        </p>
      )}

      {/* Category & Tags */}
      <div className="flex flex-wrap gap-2 mb-3">
        {document.ai_category && (
          <span
            className="px-2 py-1 text-xs rounded-full font-medium"
            style={{
              backgroundColor: `${document.ai_category.color}20`,
              color: document.ai_category.color,
            }}
          >
            {document.ai_category.name}
          </span>
        )}
        {document.ai_tags?.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="px-2 py-1 text-xs rounded-full bg-dark-700 text-dark-300"
          >
            #{tag}
          </span>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-dark-400">
        <div className="flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          <span>{formatRelativeTime(document.upload_date)}</span>
        </div>
        
        {document.processing_status === 'processing' && (
          <span className="flex items-center gap-1 text-accent-blue">
            <span className="w-2 h-2 rounded-full bg-accent-blue animate-pulse" />
            Processing...
          </span>
        )}
      </div>
    </div>
  );
}
```

### Task 9: Document Detail Panel

```typescript
// src/components/documents/DocumentDetail.tsx

import React from 'react';
import { X, Star, Download, Trash2, ExternalLink, Users, MapPin, Building, Calendar as CalendarIcon } from 'lucide-react';
import { Document } from '../../types/document';
import { Button } from '../ui/Button';
import { formatDateTime, formatFileSize } from '../../utils/formatters';
import { useSimilarDocuments } from '../../hooks/useDocuments';

interface DocumentDetailProps {
  document: Document;
  onClose: () => void;
  onFavorite: () => void;
  onDelete: () => void;
}

export function DocumentDetail({ document, onClose, onFavorite, onDelete }: DocumentDetailProps) {
  const { data: similarDocs } = useSimilarDocuments(document.id);

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-2/3 lg:w-1/2 bg-dark-900 border-l border-dark-700 overflow-y-auto z-50 animate-slide-in-right">
      {/* Header */}
      <div className="sticky top-0 bg-dark-900 border-b border-dark-700 p-6 flex items-center justify-between z-10">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <h2 className="text-xl font-display font-bold truncate">{document.filename}</h2>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={onFavorite}
          >
            <Star className={cn('w-5 h-5', document.is_favorite && 'fill-current text-accent-yellow')} />
          </Button>
          <Button variant="ghost" size="sm">
            <Download className="w-5 h-5" />
          </Button>
          <Button variant="ghost" size="sm" onClick={onDelete}>
            <Trash2 className="w-5 h-5 text-accent-red" />
          </Button>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        {/* Metadata */}
        <div className="grid grid-cols-2 gap-4 card">
          <div>
            <p className="text-sm text-dark-400">Size</p>
            <p className="font-medium">{formatFileSize(document.file_size)}</p>
          </div>
          <div>
            <p className="text-sm text-dark-400">Type</p>
            <p className="font-medium uppercase">{document.file_type}</p>
          </div>
          <div>
            <p className="text-sm text-dark-400">Source</p>
            <p className="font-medium capitalize">{document.source}</p>
          </div>
          <div>
            <p className="text-sm text-dark-400">Uploaded</p>
            <p className="font-medium">{formatDateTime(document.upload_date)}</p>
          </div>
        </div>

        {/* Summary */}
        {document.summary && (
          <div className="card">
            <h3 className="font-display font-bold mb-3">Summary</h3>
            <p className="text-dark-200 leading-relaxed">{document.summary}</p>
          </div>
        )}

        {/* Key Points */}
        {document.key_points && document.key_points.length > 0 && (
          <div className="card">
            <h3 className="font-display font-bold mb-3">Key Points</h3>
            <ul className="space-y-2">
              {document.key_points.map((point, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-accent-blue mt-1">•</span>
                  <span className="text-dark-200">{point}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Entities */}
        {document.entities && (
          <div className="card space-y-4">
            <h3 className="font-display font-bold">Entities</h3>
            
            {document.entities.people && document.entities.people.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Users className="w-4 h-4 text-accent-blue" />
                  <p className="text-sm font-medium text-dark-300">People</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {document.entities.people.map((person) => (
                    <span key={person} className="px-2 py-1 bg-dark-800 rounded text-sm">
                      {person}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {document.entities.organizations && document.entities.organizations.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Building className="w-4 h-4 text-accent-green" />
                  <p className="text-sm font-medium text-dark-300">Organizations</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {document.entities.organizations.map((org) => (
                    <span key={org} className="px-2 py-1 bg-dark-800 rounded text-sm">
                      {org}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {document.entities.locations && document.entities.locations.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <MapPin className="w-4 h-4 text-accent-red" />
                  <p className="text-sm font-medium text-dark-300">Locations</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {document.entities.locations.map((location) => (
                    <span key={location} className="px-2 py-1 bg-dark-800 rounded text-sm">
                      {location}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Action Items */}
        {document.action_items && document.action_items.length > 0 && (
          <div className="card">
            <h3 className="font-display font-bold mb-3">Action Items</h3>
            <div className="space-y-3">
              {document.action_items.map((item, index) => (
                <div key={index} className="p-3 bg-dark-800 rounded-lg">
                  <div className="flex items-start justify-between">
                    <p className="text-dark-100 flex-1">{item.text}</p>
                    {item.priority && (
                      <span
                        className={cn(
                          'px-2 py-0.5 text-xs rounded uppercase font-medium',
                          item.priority === 'high' && 'bg-accent-red/20 text-accent-red',
                          item.priority === 'medium' && 'bg-accent-yellow/20 text-accent-yellow',
                          item.priority === 'low' && 'bg-accent-green/20 text-accent-green'
                        )}
                      >
                        {item.priority}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 mt-2 text-sm text-dark-400">
                    {item.assignee && <span>👤 {item.assignee}</span>}
                    {item.due_date && (
                      <span className="flex items-center gap-1">
                        <CalendarIcon className="w-3 h-3" />
                        {formatDateTime(item.due_date)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Similar Documents */}
        {similarDocs && similarDocs.similar_documents.length > 0 && (
          <div className="card">
            <h3 className="font-display font-bold mb-3">Similar Documents</h3>
            <div className="space-y-2">
              {similarDocs.similar_documents.map((similar) => (
                <div key={similar.document.id} className="p-3 bg-dark-800 rounded-lg hover:bg-dark-700 cursor-pointer transition-colors">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-dark-100">{similar.document.filename}</p>
                    <span className="text-sm text-dark-400">
                      {Math.round(similar.similarity_score * 100)}% similar
                    </span>
                  </div>
                  {similar.document.summary && (
                    <p className="text-sm text-dark-400 mt-1 line-clamp-1">
                      {similar.document.summary}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## PART 3: SEARCH & TIMELINE (WEEK 28)

### Task 10: Search Bar with Suggestions

```typescript
// src/components/search/SearchBar.tsx

import React, { useState, useEffect, useRef } from 'react';
import { Search, X, Sparkles } from 'lucide-react';
import { useSearchStore } from '../../store/useSearchStore';
import { useSearchSuggestions } from '../../hooks/useSearch';
import { Input } from '../ui/Input';
import { cn } from '../../utils/cn';

export function SearchBar() {
  const { query, setQuery, searchMode, setSearchMode } = useSearchStore();
  const [localQuery, setLocalQuery] = useState(query);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const { data: suggestions } = useSearchSuggestions(localQuery);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (localQuery !== query) {
        setQuery(localQuery);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [localQuery]);

  const handleSelectSuggestion = (suggestion: string) => {
    setLocalQuery(suggestion);
    setQuery(suggestion);
    setShowSuggestions(false);
  };

  return (
    <div className="relative w-full max-w-2xl">
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
        <input
          ref={inputRef}
          type="text"
          value={localQuery}
          onChange={(e) => {
            setLocalQuery(e.target.value);
            setShowSuggestions(true);
          }}
          onFocus={() => setShowSuggestions(true)}
          placeholder="Search documents..."
          className="w-full pl-12 pr-32 py-3 bg-dark-800 border border-dark-700 rounded-xl text-dark-50 placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-accent-blue/50 transition-all"
        />
        
        {/* Mode Toggle */}
        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2">
          <button
            onClick={() => setSearchMode(searchMode === 'keyword' ? 'semantic' : 'keyword')}
            className={cn(
              'flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
              searchMode === 'semantic'
                ? 'bg-accent-purple text-white'
                : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
            )}
          >
            {searchMode === 'semantic' && <Sparkles className="w-4 h-4" />}
            {searchMode === 'semantic' ? 'Semantic' : 'Keyword'}
          </button>
          
          {localQuery && (
            <button
              onClick={() => {
                setLocalQuery('');
                setQuery('');
                inputRef.current?.focus();
              }}
              className="p-1.5 hover:bg-dark-700 rounded-lg transition-colors"
            >
              <X className="w-4 h-4 text-dark-400" />
            </button>
          )}
        </div>
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions && suggestions.suggestions.length > 0 && localQuery.length >= 2 && (
        <div className="absolute z-50 w-full mt-2 bg-dark-800 border border-dark-700 rounded-xl shadow-2xl overflow-hidden">
          {suggestions.suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSelectSuggestion(suggestion)}
              className="w-full px-4 py-3 text-left hover:bg-dark-700 transition-colors flex items-center gap-2 text-dark-100"
            >
              <Search className="w-4 h-4 text-dark-400" />
              <span>{suggestion}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

### Task 11: Timeline View

```typescript
// src/components/timeline/Timeline.tsx

import React, { useMemo } from 'react';
import { Virtuoso } from 'react-virtuoso';
import { format, startOfDay, endOfDay } from 'date-fns';
import { Document } from '../../types/document';
import { DocumentCard } from '../documents/DocumentCard';

interface TimelineProps {
  documents: Document[];
  onDocumentClick: (doc: Document) => void;
  onFavorite: (doc: Document) => void;
}

export function Timeline({ documents, onDocumentClick, onFavorite }: TimelineProps) {
  // Group documents by date
  const groupedDocs = useMemo(() => {
    const groups: Record<string, Document[]> = {};
    
    documents.forEach((doc) => {
      const date = format(new Date(doc.upload_date), 'yyyy-MM-dd');
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(doc);
    });
    
    return Object.entries(groups)
      .sort(([a], [b]) => new Date(b).getTime() - new Date(a).getTime())
      .map(([date, docs]) => ({
        date,
        documents: docs.sort(
          (a, b) =>
            new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime()
        ),
      }));
  }, [documents]);

  return (
    <div className="h-full">
      <Virtuoso
        data={groupedDocs}
        itemContent={(index, group) => (
          <div className="mb-8">
            {/* Date Header */}
            <div className="sticky top-0 z-10 bg-dark-900/95 backdrop-blur-sm border-b border-dark-700 py-3 mb-4">
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-dark-700" />
                <h3 className="font-display font-bold text-lg">
                  {format(new Date(group.date), 'MMMM dd, yyyy')}
                </h3>
                <div className="flex-1 h-px bg-dark-700" />
                <span className="text-sm text-dark-400 bg-dark-800 px-3 py-1 rounded-full">
                  {group.documents.length} {group.documents.length === 1 ? 'document' : 'documents'}
                </span>
              </div>
            </div>

            {/* Documents */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {group.documents.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onClick={() => onDocumentClick(doc)}
                  onFavorite={() => onFavorite(doc)}
                />
              ))}
            </div>
          </div>
        )}
      />
    </div>
  );
}
```

---

## PART 4: VIEWS & PAGES (WEEK 29-30)

### Task 12: Home Page

```typescript
// src/views/HomePage.tsx

import React, { useState } from 'react';
import { useDocuments } from '../hooks/useDocuments';
import { DocumentUpload } from '../components/documents/DocumentUpload';
import { DocumentCard } from '../components/documents/DocumentCard';
import { DocumentDetail } from '../components/documents/DocumentDetail';
import { SearchBar } from '../components/search/SearchBar';
import { Document } from '../types/document';
import { useDocumentStore } from '../store/useDocumentStore';
import { TrendingUp, FileText, Star, Clock } from 'lucide-react';

export function HomePage() {
  const { data, isLoading } = useDocuments({ limit: 20 });
  const selectedDocument = useDocumentStore((state) => state.selectedDocument);
  const setSelectedDocument = useDocumentStore((state) => state.setSelectedDocument);

  const stats = {
    total: data?.total || 0,
    thisWeek: 12, // Would come from API
    favorites: 5,
    processing: 2,
  };

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <header className="border-b border-dark-700 bg-dark-900/95 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-display font-bold">Document Intelligence</h1>
              <p className="text-dark-400 mt-1">Your AI-powered knowledge base</p>
            </div>
          </div>
          
          <SearchBar />
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dark-400">Total Documents</p>
                <p className="text-2xl font-display font-bold mt-1">{stats.total}</p>
              </div>
              <FileText className="w-8 h-8 text-accent-blue" />
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dark-400">This Week</p>
                <p className="text-2xl font-display font-bold mt-1 text-accent-green">+{stats.thisWeek}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-accent-green" />
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dark-400">Favorites</p>
                <p className="text-2xl font-display font-bold mt-1 text-accent-yellow">{stats.favorites}</p>
              </div>
              <Star className="w-8 h-8 text-accent-yellow" />
            </div>
          </div>
          
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-dark-400">Processing</p>
                <p className="text-2xl font-display font-bold mt-1">{stats.processing}</p>
              </div>
              <Clock className="w-8 h-8 text-accent-purple animate-pulse-slow" />
            </div>
          </div>
        </div>

        {/* Upload */}
        <div className="mb-8">
          <DocumentUpload />
        </div>

        {/* Recent Documents */}
        <div>
          <h2 className="text-xl font-display font-bold mb-4">Recent Documents</h2>
          {isLoading ? (
            <div className="text-center py-12 text-dark-400">Loading...</div>
          ) : data && data.results.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.results.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  document={doc}
                  onClick={() => setSelectedDocument(doc)}
                  onFavorite={() => {/* Toggle favorite */}}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-dark-400">
              No documents yet. Upload your first document to get started!
            </div>
          )}
        </div>
      </main>

      {/* Detail Panel */}
      {selectedDocument && (
        <DocumentDetail
          document={selectedDocument}
          onClose={() => setSelectedDocument(null)}
          onFavorite={() => {/* Toggle favorite */}}
          onDelete={() => {/* Delete document */}}
        />
      )}
    </div>
  );
}
```

### Task 13: App Router

```typescript
// src/App.tsx

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HomePage } from './views/HomePage';
import { TimelineView } from './views/TimelineView';
import { SearchView } from './views/SearchView';
import { ConnectionsView } from './views/ConnectionsView';
import { InsightsView } from './views/InsightsView';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/timeline" element={<TimelineView />} />
          <Route path="/search" element={<SearchView />} />
          <Route path="/connections" element={<ConnectionsView />} />
          <Route path="/insights" element={<InsightsView />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

---

## TESTING & DEPLOYMENT

### Task 14: Build & Deploy

```bash
# Build for production
npm run build

# Preview production build
npm run preview

# Deploy to Vercel/Netlify
# Connect GitHub repo and auto-deploy on push
```

### Environment Variables

```bash
# .env.production
VITE_API_URL=https://api.yourdomain.com/api/v1
```

---

## SUCCESS CRITERIA

✅ **Core Infrastructure**
- API client configured
- TypeScript types complete
- State management working
- React Query hooks functional

✅ **Document Management**
- Upload works with progress
- Document cards display correctly
- Detail panel shows all info
- Favorite/delete functional

✅ **Search**
- Search bar with suggestions
- Keyword and semantic modes
- Filter system working
- Results display properly

✅ **Timeline**
- Documents grouped by date
- Virtual scrolling smooth
- Responsive grid layout
- Performance good (1000+ docs)

✅ **UI/UX**
- Dark theme implemented
- Responsive design works
- Animations smooth
- Accessible (keyboard nav)

---

## NEXT STEPS

After Phase 4, you have a **complete, production-ready platform**:

- ✅ Backend with AI (Phase 1)
- ✅ Cloud integrations (Phase 2)
- ✅ Search & intelligence (Phase 3)
- ✅ Beautiful frontend (Phase 4)

**Optional enhancements:**
- Mobile app (React Native)
- Browser extension
- Desktop app (Electron)
- Advanced visualizations
- Collaboration features

---

**Your platform is complete!** 🎉

Deploy and start using your AI-powered document intelligence system!