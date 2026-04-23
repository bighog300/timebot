# Implementation Plan - Personal Knowledge Management System

## Project Structure

```
doc-organizer/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Configuration management
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py       # Document endpoints
│   │   │   ├── categories.py      # Category endpoints
│   │   │   ├── search.py          # Search endpoints
│   │   │   └── insights.py        # AI insights endpoints
│   │   └── deps.py                # Dependency injection
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py            # Auth (future)
│   │   ├── config.py              # Settings
│   │   └── exceptions.py          # Custom exceptions
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py            # Document model
│   │   ├── category.py            # Category model
│   │   └── relationship.py        # Document relationships
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── document.py            # Pydantic schemas
│   │   ├── category.py
│   │   └── search.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_processor.py  # Text extraction
│   │   ├── ai_analyzer.py         # Claude integration
│   │   ├── categorizer.py         # Auto-categorization
│   │   ├── summarizer.py          # Document summarization
│   │   ├── search_service.py      # Search logic
│   │   └── storage.py             # File storage
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── tasks.py               # Background tasks
│   │   └── scheduler.py           # Periodic jobs
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py                # Database base
│   │   ├── session.py             # DB sessions
│   │   └── migrations/            # Alembic migrations
│   │
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py
│       ├── text_utils.py
│       └── thumbnail.py
│
├── tests/
│   ├── __init__.py
│   ├── test_api/
│   ├── test_services/
│   └── test_models/
│
├── frontend/                       # Simple web UI (optional)
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
├── scripts/
│   ├── init_db.py
│   └── migrate.py
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Database Schema (SQL)

```sql
-- documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    original_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100),
    
    -- Timestamps
    upload_date TIMESTAMP DEFAULT NOW(),
    last_modified TIMESTAMP DEFAULT NOW(),
    processed_date TIMESTAMP,
    
    -- Content
    raw_text TEXT,
    page_count INTEGER,
    word_count INTEGER,
    
    -- AI-generated content
    summary TEXT,
    key_points JSONB,
    entities JSONB,
    action_items JSONB,
    
    -- Categorization
    ai_category_id UUID REFERENCES categories(id),
    ai_confidence FLOAT,
    user_category_id UUID REFERENCES categories(id),
    
    -- Tags
    ai_tags TEXT[],
    user_tags TEXT[],
    
    -- Metadata
    extracted_metadata JSONB,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_error TEXT,
    
    -- User flags
    is_favorite BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    user_notes TEXT,
    
    -- Search
    search_vector tsvector,
    
    CONSTRAINT valid_status CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
);

-- categories table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#4A90E2',
    icon VARCHAR(50),
    
    -- Origin
    ai_generated BOOLEAN DEFAULT TRUE,
    created_by_user BOOLEAN DEFAULT FALSE,
    
    -- Stats
    document_count INTEGER DEFAULT 0,
    last_used TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- document_relationships table
CREATE TABLE document_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    target_doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT no_self_reference CHECK (source_doc_id != target_doc_id),
    CONSTRAINT valid_relationship CHECK (relationship_type IN ('similar_to', 'references', 'follows_up', 'related_to'))
);

-- processing_queue table
CREATE TABLE processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'queued',
    priority INTEGER DEFAULT 5,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_documents_category ON documents(ai_category_id);
CREATE INDEX idx_documents_user_category ON documents(user_category_id);
CREATE INDEX idx_documents_upload_date ON documents(upload_date DESC);
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_search ON documents USING GIN(search_vector);
CREATE INDEX idx_documents_tags ON documents USING GIN(ai_tags);
CREATE INDEX idx_relationships_source ON document_relationships(source_doc_id);
CREATE INDEX idx_relationships_target ON document_relationships(target_doc_id);

-- Full-text search trigger
CREATE TRIGGER documents_search_vector_update
BEFORE INSERT OR UPDATE ON documents
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.english', filename, raw_text, summary);
```

## Core Implementation Files

### 1. Document Processor Service

```python
# app/services/document_processor.py

from pathlib import Path
import pypdf2
from docx import Document
import pytesseract
from PIL import Image
import mimetypes

class DocumentProcessor:
    """Extract text and metadata from various document types"""
    
    SUPPORTED_TYPES = {
        'application/pdf': '_process_pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '_process_docx',
        'text/plain': '_process_text',
        'image/png': '_process_image',
        'image/jpeg': '_process_image',
    }
    
    async def process(self, file_path: Path) -> dict:
        """
        Process a document and extract content
        Returns: {
            'text': str,
            'page_count': int,
            'word_count': int,
            'metadata': dict
        }
        """
        mime_type = mimetypes.guess_type(file_path)[0]
        
        if mime_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"Unsupported file type: {mime_type}")
        
        processor_method = getattr(self, self.SUPPORTED_TYPES[mime_type])
        return await processor_method(file_path)
    
    async def _process_pdf(self, file_path: Path) -> dict:
        """Extract text from PDF"""
        with open(file_path, 'rb') as f:
            pdf = pypdf2.PdfReader(f)
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            
            return {
                'text': text,
                'page_count': len(pdf.pages),
                'word_count': len(text.split()),
                'metadata': pdf.metadata or {}
            }
    
    async def _process_docx(self, file_path: Path) -> dict:
        """Extract text from Word document"""
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        
        return {
            'text': text,
            'page_count': 1,  # DOCX doesn't have page concept easily
            'word_count': len(text.split()),
            'metadata': doc.core_properties.__dict__ if hasattr(doc, 'core_properties') else {}
        }
    
    async def _process_text(self, file_path: Path) -> dict:
        """Extract text from plain text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        return {
            'text': text,
            'page_count': 1,
            'word_count': len(text.split()),
            'metadata': {}
        }
    
    async def _process_image(self, file_path: Path) -> dict:
        """Extract text from image using OCR"""
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        
        return {
            'text': text,
            'page_count': 1,
            'word_count': len(text.split()),
            'metadata': {
                'width': image.width,
                'height': image.height,
                'format': image.format
            }
        }
```

### 2. AI Analyzer Service

```python
# app/services/ai_analyzer.py

from anthropic import Anthropic
import json
from typing import Dict, List, Optional

class AIAnalyzer:
    """Claude-powered document analysis"""
    
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    async def analyze_document(
        self, 
        text: str, 
        filename: str,
        existing_categories: List[str]
    ) -> Dict:
        """
        Comprehensive document analysis
        Returns structured data about the document
        """
        
        prompt = self._build_analysis_prompt(text, filename, existing_categories)
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse JSON response
        response_text = message.content[0].text
        
        # Claude sometimes wraps JSON in markdown, clean it
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        
        return json.loads(response_text.strip())
    
    def _build_analysis_prompt(
        self, 
        text: str, 
        filename: str,
        existing_categories: List[str]
    ) -> str:
        """Build the prompt for document analysis"""
        
        # Truncate text if too long (keep first 4000 chars for context)
        text_sample = text[:4000] if len(text) > 4000 else text
        
        return f"""Analyze this document and provide structured insights.

FILENAME: {filename}

DOCUMENT CONTENT:
{text_sample}

EXISTING CATEGORIES:
{', '.join(existing_categories) if existing_categories else 'None yet - suggest appropriate categories'}

Provide a JSON response with this exact structure:
{{
  "summary": "A concise 3-5 sentence summary of the document",
  "document_type": "report|note|article|reference|receipt|form|letter|other",
  "suggested_category": "Most appropriate existing category OR new category name",
  "category_confidence": 0.85,
  "create_new_category": false,
  "new_category_description": "Only if create_new_category is true",
  "tags": ["relevant", "tag", "keywords"],
  "key_points": [
    "Most important point 1",
    "Most important point 2",
    "Most important point 3"
  ],
  "entities": {{
    "people": ["names mentioned"],
    "organizations": ["companies, institutions"],
    "dates": ["important dates"],
    "locations": ["places mentioned"]
  }},
  "action_items": [
    "Any tasks or actions mentioned"
  ],
  "sentiment": "neutral|positive|negative|mixed",
  "language": "en",
  "topics": ["main", "subject", "areas"]
}}

Important:
- Be concise and accurate
- Only suggest creating a new category if the content is clearly distinct from existing ones
- Extract only explicit action items, don't infer
- Use confidence score honestly (0.0-1.0)
- Return ONLY valid JSON, no additional text"""
    
    async def suggest_categories(
        self, 
        document_summaries: List[Dict]
    ) -> List[Dict]:
        """
        Analyze multiple documents to suggest initial category structure
        """
        
        prompt = f"""Based on these document summaries, suggest 5-10 natural categories that would organize them effectively.

DOCUMENTS:
{json.dumps(document_summaries, indent=2)}

Suggest categories that:
1. Reflect actual content patterns
2. Are mutually exclusive where possible
3. Have clear, user-friendly names
4. Will scale as more documents are added
5. Avoid being too granular (not "Work Emails" and "Personal Emails" - just "Emails")

Return JSON array:
[
  {{
    "name": "Category Name",
    "description": "What types of documents go here",
    "color": "#hex color code",
    "example_docs": ["doc1", "doc2"]
  }}
]

Return ONLY valid JSON."""
        
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        
        return json.loads(response_text.strip())
```

### 3. Background Tasks

```python
# app/workers/tasks.py

from celery import Celery
from app.services.document_processor import DocumentProcessor
from app.services.ai_analyzer import AIAnalyzer
from app.db.session import get_db
from app.models.document import Document
from app.core.config import settings

celery_app = Celery(
    "doc_organizer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """
    Background task to process uploaded document
    """
    try:
        db = next(get_db())
        doc = db.query(Document).filter(Document.id == document_id).first()
        
        if not doc:
            return {"error": "Document not found"}
        
        # Update status
        doc.processing_status = "processing"
        db.commit()
        
        # 1. Extract text
        processor = DocumentProcessor()
        extracted = await processor.process(Path(doc.original_path))
        
        doc.raw_text = extracted['text']
        doc.page_count = extracted['page_count']
        doc.word_count = extracted['word_count']
        doc.extracted_metadata = extracted['metadata']
        db.commit()
        
        # 2. AI analysis
        analyzer = AIAnalyzer(settings.ANTHROPIC_API_KEY)
        
        # Get existing categories
        categories = db.query(Category).all()
        category_names = [c.name for c in categories]
        
        analysis = await analyzer.analyze_document(
            text=doc.raw_text,
            filename=doc.filename,
            existing_categories=category_names
        )
        
        # 3. Update document with analysis
        doc.summary = analysis['summary']
        doc.key_points = analysis['key_points']
        doc.entities = analysis['entities']
        doc.action_items = analysis['action_items']
        doc.ai_tags = analysis['tags']
        
        # 4. Handle categorization
        if analysis['create_new_category']:
            # Create new category
            new_category = Category(
                name=analysis['suggested_category'],
                description=analysis.get('new_category_description'),
                ai_generated=True
            )
            db.add(new_category)
            db.commit()
            doc.ai_category_id = new_category.id
        else:
            # Find existing category
            category = db.query(Category).filter(
                Category.name == analysis['suggested_category']
            ).first()
            if category:
                doc.ai_category_id = category.id
        
        doc.ai_confidence = analysis['category_confidence']
        doc.processing_status = "completed"
        doc.processed_date = datetime.utcnow()
        
        db.commit()
        
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        doc.processing_status = "failed"
        doc.processing_error = str(e)
        db.commit()
        
        # Retry
        raise self.retry(exc=e, countdown=60)
```

## API Implementation Priority

### Phase 1 - Core Upload & Processing
1. ✅ `POST /api/v1/documents/upload` - Upload document
2. ✅ `GET /api/v1/documents/{id}` - Get document details
3. ✅ `GET /api/v1/documents` - List documents (paginated)
4. ✅ `GET /api/v1/categories` - List categories

### Phase 2 - Intelligence
5. `GET /api/v1/documents/{id}/related` - Find related documents
6. `POST /api/v1/search` - Full-text search
7. `GET /api/v1/insights/summary` - Daily/weekly insights

### Phase 3 - User Control
8. `PUT /api/v1/documents/{id}` - Update document (user tags, notes)
9. `POST /api/v1/categories` - Create manual category
10. `PUT /api/v1/documents/{id}/category` - Reassign category

## Testing Strategy

```python
# tests/test_services/test_ai_analyzer.py

import pytest
from app.services.ai_analyzer import AIAnalyzer

@pytest.mark.asyncio
async def test_document_analysis():
    analyzer = AIAnalyzer(api_key="test-key")
    
    sample_text = """
    Meeting Notes - Q1 Planning
    Date: January 15, 2026
    
    Discussed launch strategy for new product.
    Action items:
    - John to prepare market analysis by Jan 30
    - Sarah to draft marketing plan
    """
    
    result = await analyzer.analyze_document(
        text=sample_text,
        filename="meeting-notes.txt",
        existing_categories=["Work", "Personal"]
    )
    
    assert result['document_type'] == 'note'
    assert len(result['action_items']) == 2
    assert 'Work' in result['suggested_category']
```

## Deployment Checklist

- [ ] Database migrations created
- [ ] Redis configured for Celery
- [ ] Environment variables set
- [ ] API documentation generated (FastAPI auto-docs)
- [ ] Background worker running
- [ ] File storage permissions correct
- [ ] Health check endpoint working
- [ ] Logging configured
- [ ] Error tracking setup (Sentry optional)
- [ ] Backup strategy for documents

## Next Development Steps

1. **Implement Document Processor** - Get text extraction working
2. **Build AI Analyzer** - Integration with Claude API
3. **Create Database Models** - SQLAlchemy models
4. **API Endpoints** - FastAPI routes
5. **Background Workers** - Celery tasks
6. **Simple Web UI** - Testing interface
7. **Mobile API Optimization** - Prepare for React Native
