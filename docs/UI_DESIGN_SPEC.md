# Document Intelligence Platform - UI/UX Design Specification

## Product Vision

**An intelligent document timeline system that connects to your cloud storage (Gmail, Google Drive, Dropbox), automatically inventories everything, creates GPT-ready summaries, and presents your entire document history as an explorable, searchable timeline.**

## Design Philosophy

**Aesthetic Direction: "Information Cartography"**
- Clean, data-rich interface inspired by modern mapping/analytics tools
- Sophisticated neutral palette with vibrant accent colors for categories
- Timeline-first navigation (chronological river of documents)
- Generous whitespace with dense information clusters
- Motion that reveals relationships and context

**Core Metaphor**: Your documents as a **living map** of your digital life that you can explore through time and context.

## UI Architecture

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  HEADER: Logo | Search | View Toggle | Connections | Profile   │
├───────┬─────────────────────────────────────────────────────────┤
│       │                                                         │
│       │                 MAIN CONTENT AREA                       │
│  S    │  ┌─────────────────────────────────────────────────┐  │
│  I    │  │                                                 │  │
│  D    │  │         Timeline View / Grid View /             │  │
│  E    │  │         Category View / Search Results          │  │
│  B    │  │                                                 │  │
│  A    │  │                                                 │  │
│  R    │  └─────────────────────────────────────────────────┘  │
│       │                                                         │
│  - Timeline                                                     │
│  - Categories                                                   │
│  - Sources                                                      │
│  - Filters                                                      │
│  - Insights                                                     │
└───────┴─────────────────────────────────────────────────────────┘
```

## Key Views & Components

### 1. Dashboard / Timeline View (Primary)

**The Document River** - Horizontal or vertical scrolling timeline showing all documents chronologically.

```
┌──────────────────────────────────────────────────────┐
│  📅 Timeline Scrubber                                │
│  [====•==========================================] →  │
│       ↑                                              │
│   April 2026                                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  🔵 April 19, 2026                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  │ 📄 File 1  │  │ 📧 Email 2 │  │ 📊 Sheet 3 │    │
│  │ Work       │  │ Personal   │  │ Finance    │    │
│  │ Summary... │  │ Summary... │  │ Summary... │    │
│  └────────────┘  └────────────┘  └────────────┘    │
│                                                      │
│  🔵 April 18, 2026                                   │
│  ┌────────────┐  ┌────────────┐                     │
│  │ 📄 File 4  │  │ 🖼️ Image 5│                     │
│  │ Projects   │  │ Travel     │                     │
│  │ Summary... │  │ Summary... │                     │
│  └────────────┘  └────────────┘                     │
│                                                      │
│  🔵 April 15, 2026                                   │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐    │
│  ...                                                 │
└──────────────────────────────────────────────────────┘
```

**Features:**
- Infinite scroll through time
- Date clusters collapse/expand
- Hover reveals full summary
- Click opens detail panel
- Drag to reposition in timeline
- Multi-select for batch actions

### 2. Connection Management View

**Cloud Source Dashboard** - Visual status of all connected services

```
┌──────────────────────────────────────────────────────┐
│  Connected Sources                    [+ Add Source] │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ✅ Gmail                          🔄 Syncing (67%)  │
│  ├─ Last sync: 2 minutes ago                        │
│  ├─ Documents: 1,247 emails                         │
│  ├─ Status: Healthy                                 │
│  └─ [Settings] [Disconnect]                         │
│                                                      │
│  ✅ Google Drive                   ✓ Up to date     │
│  ├─ Last sync: 5 minutes ago                        │
│  ├─ Documents: 3,842 files                          │
│  ├─ Status: Healthy                                 │
│  └─ [Settings] [Disconnect]                         │
│                                                      │
│  ✅ Dropbox                        ✓ Up to date     │
│  ├─ Last sync: 1 hour ago                           │
│  ├─ Documents: 592 files                            │
│  ├─ Status: Healthy                                 │
│  └─ [Settings] [Disconnect]                         │
│                                                      │
│  ⚪ OneDrive                       [Connect]         │
│  └─ Not connected                                   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 3. Document Detail Panel (Slide-in)

**Deep Dive View** - Everything about a single document

```
┌──────────────────────────────────────────────────────┐
│  [← Back]              Document Details        [✕]   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  📄 meeting-notes-q1-planning.pdf                    │
│  🔵 Work Projects                                    │
│                                                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                      │
│  📊 Metadata                                         │
│  • Source: Google Drive                             │
│  • Created: January 15, 2026                        │
│  • Modified: January 16, 2026                       │
│  • Size: 245 KB                                     │
│  • Type: PDF                                        │
│                                                      │
│  📝 AI Summary                          [Regenerate] │
│  ┌──────────────────────────────────────────────┐   │
│  │ Q1 planning meeting notes discussing launch  │   │
│  │ strategy for new product line. Team agreed   │   │
│  │ on market positioning and timeline. Key      │   │
│  │ decisions include budget allocation and      │   │
│  │ marketing approach for target demographics.  │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  🎯 Key Points                                       │
│  • Launch planned for March 2026                    │
│  • Budget approved: $150K                           │
│  • Target market: 25-40 age group                   │
│  • Marketing channels: Social, Content, Events      │
│                                                      │
│  ✅ Action Items                                     │
│  • John: Market analysis by Jan 30                  │
│  • Sarah: Draft marketing plan                      │
│  • Team: Review positioning statement               │
│                                                      │
│  👤 People Mentioned                                 │
│  John Smith, Sarah Johnson, Marketing Team          │
│                                                      │
│  🔗 Related Documents (3)                            │
│  ┌─────────────────────────────────────────────┐    │
│  │ 📊 Q1 Budget Spreadsheet                    │    │
│  │ 📄 Market Research Report                   │    │
│  │ 📧 Email: Product Launch Discussion         │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  🏷️ Tags                                            │
│  [planning] [Q1] [product-launch] [meeting]         │
│  [+ Add tag]                                        │
│                                                      │
│  💬 Notes                              [Edit]       │
│  ┌──────────────────────────────────────────────┐   │
│  │ Your personal notes here...                  │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  📥 Actions                                          │
│  [View Original] [Download] [Share] [Archive]       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 4. Category Explorer

**Visual category breakdown** with smart groupings

```
┌──────────────────────────────────────────────────────┐
│  Categories                         [Manage]         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  🔵 Work Projects                              847   │
│  ┌────────────────────────────────────────────────┐ │
│  │ Recent: Product Launch Planning, Q1 Review,   │ │
│  │ Team Meeting Notes...                         │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  🟢 Personal                                    423   │
│  ┌────────────────────────────────────────────────┐ │
│  │ Recent: Travel Itinerary, Recipe Collection,  │ │
│  │ Home Improvement...                           │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  🟡 Finance                                     156   │
│  ┌────────────────────────────────────────────────┐ │
│  │ Recent: Tax Documents, Bank Statements,       │ │
│  │ Investment Reports...                         │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  🟣 Health & Medical                            89    │
│  🔴 Legal Documents                             45    │
│  🟠 Travel & Trips                              134   │
│  ⚫ Uncategorized                               23    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 5. Semantic Search Interface

**Natural language search** with AI-powered results

```
┌──────────────────────────────────────────────────────┐
│  🔍 Search your documents...                         │
│  ┌──────────────────────────────────────────────┐   │
│  │ Find my dentist appointment from last month  │ 🔍 │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  💡 AI Understanding:                                │
│  Looking for: medical appointments, dental,          │
│  timeframe: March 2026                               │
│                                                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                      │
│  📧 Dentist Appointment Confirmation                 │
│  🟣 Health & Medical • March 15, 2026               │
│  "Your appointment with Dr. Smith is confirmed       │
│   for March 28, 2026 at 2:00 PM for routine..."     │
│  Relevance: ████████░░ 85%                          │
│                                                      │
│  📄 Dental Insurance Coverage                        │
│  🟡 Finance • March 1, 2026                         │
│  "Annual dental coverage includes cleanings,         │
│   x-rays, and basic procedures. Deductible..."      │
│  Relevance: ██████░░░░ 62%                          │
│                                                      │
│  🔗 View 3 more results                              │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 6. Insights Dashboard

**AI-generated insights** about your document collection

```
┌──────────────────────────────────────────────────────┐
│  📊 Insights                                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  💡 This Week                                        │
│  • 23 new documents added                           │
│  • 8 action items detected across documents         │
│  • Most active category: Work Projects              │
│  • 3 upcoming deadlines mentioned                   │
│                                                      │
│  📈 Trends                                           │
│  ┌────────────────────────────────────────────────┐ │
│  │     Documents by Category (Last 30 Days)       │ │
│  │  ┌─┐                                            │ │
│  │  │█│    ┌─┐                                     │ │
│  │  │█│    │█│    ┌─┐                              │ │
│  │  │█│┌─┐ │█│    │█│  ┌─┐                        │ │
│  │  └─┘└─┘ └─┘    └─┘  └─┘                        │ │
│  │  Work Pers Fin  Hlth Trvl                       │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  ⚠️ Action Required                                  │
│  • "Market analysis due Jan 30" - 11 days away      │
│  • "Review Q1 budget" - mentioned in 3 docs         │
│  • "Tax documents needed" - April 15 deadline       │
│                                                      │
│  🔗 Connections Discovered                           │
│  • Found 12 documents related to "Product Launch"   │
│  • 5 email threads connected to meetings            │
│  • Budget docs linked to planning documents         │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## Color System

```css
/* Base Theme - Information Cartography */
--bg-primary: #0F1419;           /* Deep charcoal */
--bg-secondary: #1A1F29;         /* Slightly lighter */
--bg-tertiary: #242B38;          /* Card backgrounds */

--text-primary: #E8EAED;         /* Off-white */
--text-secondary: #9BA3AF;       /* Muted text */
--text-tertiary: #6B7280;        /* Subtle text */

--accent-primary: #3B82F6;       /* Bright blue - primary actions */
--accent-success: #10B981;       /* Green - positive states */
--accent-warning: #F59E0B;       /* Amber - warnings */
--accent-danger: #EF4444;        /* Red - errors */

/* Category Colors (vibrant, distinguishable) */
--category-work: #3B82F6;        /* Blue */
--category-personal: #10B981;    /* Green */
--category-finance: #F59E0B;     /* Amber */
--category-health: #8B5CF6;      /* Purple */
--category-legal: #EF4444;       /* Red */
--category-travel: #F97316;      /* Orange */
--category-education: #06B6D4;   /* Cyan */
--category-misc: #6B7280;        /* Gray */

/* Gradients */
--gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
--gradient-success: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
--gradient-mesh: radial-gradient(at 40% 20%, rgba(59, 130, 246, 0.15) 0px, transparent 50%),
                  radial-gradient(at 80% 0%, rgba(139, 92, 246, 0.15) 0px, transparent 50%);

/* Shadows & Depth */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.6);

/* Border */
--border-subtle: 1px solid rgba(255, 255, 255, 0.1);
--border-default: 1px solid rgba(255, 255, 255, 0.15);
```

## Typography

```css
/* Font Stack - Distinctive & Readable */
--font-display: 'Space Mono', 'Courier New', monospace;  /* Headers - technical feel */
--font-body: 'Inter', -apple-system, system-ui, sans-serif;  /* Body text */
--font-mono: 'JetBrains Mono', 'Consolas', monospace;  /* Code/data */

/* Type Scale */
--text-xs: 0.75rem;      /* 12px */
--text-sm: 0.875rem;     /* 14px */
--text-base: 1rem;       /* 16px */
--text-lg: 1.125rem;     /* 18px */
--text-xl: 1.25rem;      /* 20px */
--text-2xl: 1.5rem;      /* 24px */
--text-3xl: 1.875rem;    /* 30px */
--text-4xl: 2.25rem;     /* 36px */

/* Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

## Animation & Motion

```css
/* Timing Functions */
--ease-smooth: cubic-bezier(0.4, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
--ease-sharp: cubic-bezier(0.4, 0, 0.6, 1);

/* Durations */
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 350ms;

/* Animations */
@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

## Component Specifications

### Document Card

```html
<div class="document-card">
  <div class="card-header">
    <span class="document-icon">📄</span>
    <span class="category-badge">Work</span>
  </div>
  
  <h3 class="document-title">meeting-notes.pdf</h3>
  
  <p class="document-summary">
    Q1 planning meeting notes discussing launch strategy...
  </p>
  
  <div class="card-meta">
    <span class="meta-date">Apr 19, 2026</span>
    <span class="meta-source">Google Drive</span>
  </div>
  
  <div class="card-actions">
    <button class="btn-icon">👁️</button>
    <button class="btn-icon">⭐</button>
    <button class="btn-icon">🔗</button>
  </div>
</div>
```

### Timeline Scrubber

```html
<div class="timeline-scrubber">
  <div class="scrubber-track">
    <div class="scrubber-progress" style="width: 35%"></div>
    <div class="scrubber-handle" style="left: 35%">
      <span class="handle-date">Apr 2026</span>
    </div>
  </div>
  
  <div class="timeline-markers">
    <span class="marker" data-date="2026-01">Jan</span>
    <span class="marker" data-date="2026-02">Feb</span>
    <span class="marker active" data-date="2026-04">Apr</span>
    <span class="marker" data-date="2026-06">Jun</span>
  </div>
</div>
```

### Connection Status Card

```html
<div class="connection-card status-active">
  <div class="connection-header">
    <img src="gmail-icon.svg" class="service-icon" />
    <h4>Gmail</h4>
    <span class="status-badge syncing">Syncing 67%</span>
  </div>
  
  <div class="connection-stats">
    <div class="stat">
      <span class="stat-label">Last sync</span>
      <span class="stat-value">2 min ago</span>
    </div>
    <div class="stat">
      <span class="stat-label">Documents</span>
      <span class="stat-value">1,247</span>
    </div>
  </div>
  
  <div class="progress-bar">
    <div class="progress-fill" style="width: 67%"></div>
  </div>
  
  <div class="connection-actions">
    <button class="btn-secondary">Settings</button>
    <button class="btn-ghost">Disconnect</button>
  </div>
</div>
```

## Responsive Breakpoints

```css
/* Mobile First */
--breakpoint-sm: 640px;   /* Small tablets */
--breakpoint-md: 768px;   /* Tablets */
--breakpoint-lg: 1024px;  /* Laptops */
--breakpoint-xl: 1280px;  /* Desktops */
--breakpoint-2xl: 1536px; /* Large screens */
```

## Accessibility Requirements

- WCAG 2.1 Level AA compliance
- Keyboard navigation for all interactive elements
- Screen reader optimized labels
- Focus states clearly visible
- Color contrast ratios > 4.5:1
- Reduced motion preferences respected

## Performance Targets

- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- Largest Contentful Paint: < 2.5s
- Virtual scrolling for timeline (render only visible items)
- Lazy load document thumbnails
- Service Worker for offline functionality

## Next Steps

This specification defines the visual and interaction design. Next documents needed:

1. **Component Library** - React components implementation
2. **State Management** - Redux/Zustand architecture
3. **API Integration** - Frontend service layer
4. **Routing & Navigation** - Page structure
5. **Build Configuration** - Webpack/Vite setup
