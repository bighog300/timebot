# Personal Knowledge Management System - Architecture

## Overview
A mobile-first personal knowledge management system with AI-powered auto-categorization, summarization, and intelligent organization.

## Core Philosophy
- **Zero-friction capture**: Upload anything, AI handles the rest
- **Intelligent organization**: Categories emerge from your documents, not forced hierarchies
- **Mobile-ready**: API-first design for eventual mobile app
- **Privacy-first**: Self-hosted, your data stays yours

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Mobile App (Future)                  │
│                     Web Interface                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ REST API
                     │
┌────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌──────────────┬──────────────┬────────────────────┐  │
│  │   Document   │  AI Analysis │    Search &        │  │
│  │   Processor  │   Service    │    Retrieval       │  │
│  └──────────────┴──────────────┴────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼───┐   ┌───▼────┐  ┌───▼────────┐
   │PostgreSQL│   │ Redis  │  │ Vector DB │
   │Documents │   │ Cache  │  │(Embeddings)│
   └──────────┘   └────────┘  └────────────┘
```

## Data Model

### Document Table
```sql
documents (
  id UUID PRIMARY KEY,
  filename VARCHAR(255),
  original_path TEXT,
  file_type VARCHAR(50),
  file_size BIGINT,
  upload_date TIMESTAMP,
  last_modified TIMESTAMP,
  
  -- Extracted content
  raw_text TEXT,
  extracted_metadata JSONB,
  
  -- AI-generated
  summary TEXT,
  key_points JSONB,
  ai_categories JSONB,
  ai_tags TEXT[],
  confidence_score FLOAT,
  
  -- User overrides
  user_category VARCHAR(100),
  user_tags TEXT[],
  user_notes TEXT,
  is_favorite BOOLEAN DEFAULT FALSE,
  is_archived BOOLEAN DEFAULT FALSE
)
```

### Categories Table (Auto-discovered)
```sql
categories (
  id UUID PRIMARY KEY,
  name VARCHAR(100) UNIQUE,
  description TEXT,
  ai_generated BOOLEAN DEFAULT TRUE,
  document_count INTEGER DEFAULT 0,
  created_at TIMESTAMP,
  color VARCHAR(7)  -- hex color for UI
)
```

### Document Relationships
```sql
document_links (
  source_doc_id UUID,
  target_doc_id UUID,
  relationship_type VARCHAR(50),  -- 'references', 'similar_to', 'follows_up'
  confidence FLOAT,
  PRIMARY KEY (source_doc_id, target_doc_id)
)
```

## AI Processing Pipeline

### 1. Document Ingestion
```
Upload → Extract Text → Store Raw → Queue for Processing
```

### 2. AI Analysis (Async)
```python
def analyze_document(doc_id):
    """
    Multi-stage AI analysis
    """
    # Stage 1: Quick extraction
    - Extract title, dates, entities
    - Generate summary (3-5 sentences)
    - Identify document type
    
    # Stage 2: Deep categorization
    - Analyze content themes
    - Compare with existing categories
    - Suggest new categories if needed
    - Assign confidence scores
    
    # Stage 3: Key information
    - Extract action items
    - Identify important dates
    - Pull out key quotes
    - Find related documents
    
    # Stage 4: Embedding
    - Generate vector embedding
    - Store for semantic search
```

### 3. Category Intelligence
Categories are **emergent** - the AI discovers them from your documents:

```
First 10 documents → AI analyzes patterns → Suggests initial categories
New document → Check against existing categories → Create new if >80% unique
User can merge/rename/delete categories at any time
```

Example categories that might emerge:
- "Work Projects"
- "Health & Medical"
- "Home Improvement Ideas"
- "Travel Plans"
- "Financial Documents"
- "Recipes & Cooking"

## Core Features

### Phase 1: MVP (Current)
✅ Document upload (PDF, DOCX, images, TXT)
✅ AI auto-categorization
✅ Document summarization
✅ Key info extraction
✅ Basic search
✅ REST API ready for mobile

### Phase 2: Enhanced Intelligence
- Semantic search with natural language queries
- Document relationship mapping
- Smart suggestions ("You might want to read this")
- Timeline view of documents
- OCR for scanned documents

### Phase 3: Mobile App
- Native iOS/Android apps
- Offline document viewing
- Camera capture → instant upload
- Push notifications for insights

## API Design

### RESTful Endpoints

```
POST   /api/v1/documents/upload
GET    /api/v1/documents
GET    /api/v1/documents/{id}
PUT    /api/v1/documents/{id}
DELETE /api/v1/documents/{id}

GET    /api/v1/documents/{id}/summary
GET    /api/v1/documents/{id}/related

GET    /api/v1/categories
GET    /api/v1/categories/{id}/documents
POST   /api/v1/categories (manual category)
PUT    /api/v1/categories/{id}

POST   /api/v1/search
POST   /api/v1/search/semantic

GET    /api/v1/insights/daily
GET    /api/v1/insights/trends
```

### Mobile-Optimized Responses
```json
{
  "id": "uuid",
  "filename": "meeting-notes.pdf",
  "thumbnail_url": "/thumbs/uuid.jpg",
  "summary": "Brief summary...",
  "category": {
    "id": "cat-uuid",
    "name": "Work Projects",
    "color": "#4A90E2"
  },
  "tags": ["meeting", "Q1", "strategy"],
  "upload_date": "2026-04-19T10:30:00Z",
  "file_size": 245678,
  "key_points": [
    "Action: Follow up with team by Friday",
    "Decision: Moving forward with option B",
    "Date: Next meeting April 26th"
  ]
}
```

## AI Prompting Strategy

### Document Analysis Prompt
```
Analyze this document and provide structured output:

DOCUMENT CONTENT:
{document_text}

EXISTING CATEGORIES:
{current_categories}

Provide JSON response:
{
  "summary": "3-5 sentence summary",
  "document_type": "report|note|article|reference|...",
  "suggested_category": "category name",
  "category_confidence": 0.0-1.0,
  "new_category_needed": true/false,
  "new_category_name": "if needed",
  "tags": ["tag1", "tag2", ...],
  "key_points": [
    "Important point 1",
    "Important point 2"
  ],
  "entities": {
    "people": [],
    "dates": [],
    "places": [],
    "organizations": []
  },
  "action_items": [],
  "sentiment": "neutral|positive|negative"
}
```

### Category Discovery Prompt
```
Based on these documents, identify natural groupings:

DOCUMENTS:
{batch_of_document_summaries}

Suggest 3-7 high-level categories that:
1. Reflect actual content patterns
2. Are mutually exclusive where possible
3. Have clear, user-friendly names
4. Will scale as more documents are added

Return JSON array of categories with descriptions.
```

## Storage Strategy

### File Storage
```
/app/data/
  ├── uploads/           # Original files (by date)
  │   ├── 2026/04/19/
  │   └── ...
  ├── processed/         # Extracted text, thumbnails
  │   ├── text/
  │   ├── thumbnails/
  │   └── metadata/
  └── exports/           # User-requested exports
```

### Caching Strategy
- Redis for frequently accessed summaries
- Cache AI responses for 24h
- Pre-generate thumbnails on upload
- Cache category lists (invalidate on change)

## Performance Considerations

### Async Processing
All AI analysis happens asynchronously:
1. Upload → Immediate 201 response with document ID
2. Background worker processes AI analysis
3. WebSocket/SSE updates when ready
4. Mobile app polls for completion

### Batch Processing
- Process multiple documents in parallel
- Rate limit API calls to Anthropic
- Queue system (Redis + Celery or RQ)

### Mobile Optimization
- Paginated responses (20 documents/page)
- Thumbnail generation for all file types
- Gzip compression on API responses
- CDN-ready static assets

## Security & Privacy

### Data Privacy
- All data stored locally in your instance
- No analytics or tracking
- Optional: Encryption at rest
- API key rotation support

### Authentication (Future)
- JWT tokens for mobile app
- API key for integrations
- Optional: Biometric unlock on mobile

## Scaling Considerations

### Single User Optimization
- SQLite option for ultra-lightweight deployment
- Embedded vector search (no separate Qdrant needed)
- Optional Redis (graceful degradation)

### Multi-User (Future)
- PostgreSQL required
- User isolation in DB
- Separate storage per user
- Shared category templates

## Development Roadmap

### Week 1-2: Core Foundation
- Document upload & storage ✅
- Text extraction pipeline
- Basic AI categorization
- Simple web UI

### Week 3-4: Intelligence Layer
- Smart category discovery
- Document summarization
- Key info extraction
- Related document linking

### Week 5-6: Search & Retrieval
- Vector embeddings
- Semantic search
- Timeline view
- Export functionality

### Week 7-8: Mobile Prep
- API refinement
- Response optimization
- Authentication
- Documentation

### Beyond: Mobile App
- React Native app
- Offline support
- Camera integration
- Push notifications

## Technology Stack

### Backend
- **FastAPI**: Modern async Python framework
- **SQLAlchemy**: ORM for database
- **Alembic**: Database migrations
- **Celery/RQ**: Background jobs
- **Redis**: Caching & queues

### AI/ML
- **Anthropic Claude**: Document analysis
- **Sentence Transformers**: Embeddings (future)
- **ChromaDB/Qdrant**: Vector storage (future)

### Document Processing
- **pypdf2**: PDF extraction
- **python-docx**: Word documents
- **pytesseract**: OCR
- **Pillow**: Image processing

### Future Mobile
- **React Native**: Cross-platform app
- **Expo**: Development framework
- **React Query**: API state management

## Configuration Options

Users can tune AI behavior:
```yaml
ai_config:
  auto_categorize: true
  confidence_threshold: 0.7  # Only auto-categorize if >70% confident
  max_categories: 20         # Prevent category explosion
  summarization_length: "medium"  # short/medium/long
  extract_action_items: true
  detect_duplicates: true
```

## Next Steps

1. Implement core document processor
2. Build AI analysis service
3. Create category management system
4. Develop web UI for testing
5. Mobile API hardening
6. React Native app development
