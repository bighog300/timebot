# PHASE 1 IMPLEMENTATION PROMPT FOR CURSOR/WINDSURF AI CODING ASSISTANT

## CONTEXT
You are building a **Document Intelligence Platform** - an AI-powered system that connects to cloud services (Gmail, Google Drive, Dropbox), automatically organizes documents, generates summaries, and creates a searchable timeline of all documents.

This is **Phase 1: Foundation & Core Backend** which builds the database layer, document processing pipeline, AI integration, and background task queue.

---

## PROJECT STRUCTURE TO CREATE

```
doc-organizer/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    [PROVIDED]
│   │   │   └── session.py
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py                [PROVIDED]
│   │   │   ├── document.py                [PROVIDED]
│   │   │   ├── category.py                [PROVIDED]
│   │   │   └── relationships.py           [PROVIDED]
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── document.py
│   │   │   ├── category.py
│   │   │   └── common.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── documents.py
│   │   │       ├── categories.py
│   │   │       └── health.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py      [SPRINT 2]
│   │   │   ├── text_extractor.py          [SPRINT 2]
│   │   │   ├── ai_analyzer.py             [SPRINT 3]
│   │   │   ├── summarizer.py              [SPRINT 3]
│   │   │   └── storage.py                 [SPRINT 2]
│   │   │
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py              [SPRINT 4]
│   │   │   └── tasks.py                   [SPRINT 4]
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── file_utils.py
│   │
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   │
│   ├── scripts/
│   │   ├── init_db.py
│   │   ├── seed_data.py
│   │   └── reset_db.py
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_models/
│   │
│   ├── .env.example
│   ├── requirements.txt                   [PROVIDED in repo]
│   └── README.md
│
└── schema.sql                              [PROVIDED]
```

---

## SPRINT 1: DATABASE & DATA MODELS (CURRENT SPRINT)

### OBJECTIVE
Set up PostgreSQL database, create all tables, implement SQLAlchemy models with full CRUD operations, and create migration system.

### FILES PROVIDED TO YOU
1. `schema.sql` - Complete PostgreSQL schema with all tables, indexes, triggers, and functions
2. `app/db/base.py` - SQLAlchemy engine and session configuration
3. `app/models/document.py` - Document model
4. `app/models/category.py` - Category model
5. `app/models/relationships.py` - DocumentRelationship, Connection, SyncLog, ProcessingQueue, DocumentVersion models
6. `app/models/__init__.py` - Model exports

### YOUR TASKS

#### Task 1: Initialize Database
```python
# scripts/init_db.py - CREATE THIS FILE

"""
Initialize database with schema
Run this once to create all tables
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

def create_database():
    """Create database if it doesn't exist"""
    # Connect to postgres database to create our database
    conn = psycopg2.connect(
        dbname='postgres',
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Create database
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'doc_intelligence'")
    exists = cursor.fetchone()
    if not exists:
        cursor.execute("CREATE DATABASE doc_intelligence")
        print("✓ Database 'doc_intelligence' created")
    else:
        print("✓ Database 'doc_intelligence' already exists")
    
    cursor.close()
    conn.close()

def run_schema():
    """Run schema.sql to create all tables"""
    conn = psycopg2.connect(
        dbname='doc_intelligence',
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )
    cursor = conn.cursor()
    
    # Read and execute schema.sql
    with open('schema.sql', 'r') as f:
        schema_sql = f.read()
    
    cursor.execute(schema_sql)
    conn.commit()
    print("✓ Schema created successfully")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    create_database()
    run_schema()
```

#### Task 2: Create Pydantic Schemas for API
```python
# app/schemas/document.py - CREATE THIS FILE

"""
Pydantic schemas for Document API
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class DocumentBase(BaseModel):
    filename: str
    file_type: str
    source: str = "upload"

class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    pass

class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    user_category_id: Optional[UUID] = None
    user_tags: Optional[List[str]] = None
    user_notes: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None

class DocumentResponse(DocumentBase):
    """Schema for document response"""
    id: UUID
    file_size: int
    upload_date: datetime
    processing_status: str
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    ai_tags: List[str] = []
    user_tags: List[str] = []
    is_favorite: bool = False
    is_archived: bool = False
    
    class Config:
        from_attributes = True

class DocumentDetail(DocumentResponse):
    """Detailed document response with all fields"""
    raw_text: Optional[str] = None
    entities: Optional[Dict[str, List[str]]] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    ai_category: Optional[Dict[str, Any]] = None
    related_documents: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        from_attributes = True
```

#### Task 3: Create CRUD Operations
```python
# app/crud/document.py - CREATE THIS FILE

"""
CRUD operations for documents
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from typing import List, Optional
from uuid import UUID

from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate

class DocumentCRUD:
    """CRUD operations for Document model"""
    
    def create(self, db: Session, *, obj_in: DocumentCreate, **kwargs) -> Document:
        """Create a new document"""
        db_obj = Document(
            **obj_in.model_dump(),
            **kwargs
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(self, db: Session, id: UUID) -> Optional[Document]:
        """Get document by ID"""
        return db.query(Document).filter(Document.id == id).first()
    
    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        include_archived: bool = False
    ) -> List[Document]:
        """Get multiple documents"""
        query = db.query(Document)
        
        if not include_archived:
            query = query.filter(Document.is_archived == False)
        
        return query.order_by(desc(Document.upload_date)).offset(skip).limit(limit).all()
    
    def update(self, db: Session, *, db_obj: Document, obj_in: DocumentUpdate) -> Document:
        """Update document"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, id: UUID) -> Document:
        """Delete document"""
        obj = db.query(Document).get(id)
        db.delete(obj)
        db.commit()
        return obj
    
    def search(
        self, 
        db: Session, 
        *, 
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Document]:
        """Full-text search using PostgreSQL"""
        from sqlalchemy import func
        
        return db.query(Document).filter(
            func.to_tsvector('english', Document.search_vector).match(query)
        ).order_by(
            desc(func.ts_rank(Document.search_vector, func.to_tsquery('english', query)))
        ).offset(skip).limit(limit).all()

# Create instance
document_crud = DocumentCRUD()
```

#### Task 4: Create FastAPI Endpoints
```python
# app/api/v1/documents.py - CREATE THIS FILE

"""
Document API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.api.deps import get_db
from app.crud.document import document_crud
from app.schemas.document import DocumentResponse, DocumentDetail, DocumentUpdate

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/", response_model=List[DocumentResponse])
def get_documents(
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = False,
    db: Session = Depends(get_db)
):
    """Get all documents"""
    documents = document_crud.get_multi(
        db, 
        skip=skip, 
        limit=limit,
        include_archived=include_archived
    )
    return documents

@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """Get single document by ID"""
    document = document_crud.get(db, id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document

@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: UUID,
    document_in: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """Update document"""
    document = document_crud.get(db, id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    document = document_crud.update(db, db_obj=document, obj_in=document_in)
    return document

@router.delete("/{document_id}")
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete document"""
    document = document_crud.get(db, id=document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    document_crud.delete(db, id=document_id)
    return {"message": "Document deleted successfully"}

@router.post("/search", response_model=List[DocumentResponse])
def search_documents(
    query: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Full-text search documents"""
    results = document_crud.search(db, query=query, skip=skip, limit=limit)
    return results
```

#### Task 5: Setup FastAPI Main Application
```python
# app/main.py - CREATE THIS FILE

"""
FastAPI main application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api.v1 import documents, categories
from app.db.base import init_db

# Create FastAPI app
app = FastAPI(
    title="Document Intelligence Platform API",
    description="AI-powered document organization and timeline",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    # Uncomment to auto-create tables
    # init_db()
    pass

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "doc-intelligence-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
```

#### Task 6: Create Seed Data Script
```python
# scripts/seed_data.py - CREATE THIS FILE

"""
Seed database with sample data for testing
"""

from sqlalchemy.orm import Session
from app.db.base import SessionLocal
from app.models import Category, Document
import uuid

def seed_categories(db: Session):
    """Create initial categories"""
    categories = [
        {"name": "Work", "slug": "work", "color": "#3B82F6", "icon": "💼"},
        {"name": "Personal", "slug": "personal", "color": "#10B981", "icon": "👤"},
        {"name": "Finance", "slug": "finance", "color": "#F59E0B", "icon": "💰"},
        {"name": "Health", "slug": "health", "color": "#8B5CF6", "icon": "🏥"},
    ]
    
    for cat_data in categories:
        cat = Category(**cat_data, ai_generated=True)
        db.add(cat)
    
    db.commit()
    print(f"✓ Created {len(categories)} categories")

def seed_sample_documents(db: Session):
    """Create sample documents for testing"""
    # Get a category
    category = db.query(Category).filter(Category.name == "Work").first()
    
    sample_docs = [
        {
            "filename": "meeting-notes-q1.pdf",
            "original_path": "/uploads/meeting-notes-q1.pdf",
            "file_type": "pdf",
            "file_size": 245678,
            "mime_type": "application/pdf",
            "summary": "Q1 planning meeting notes discussing product launch strategy.",
            "ai_category_id": category.id,
            "ai_tags": ["meeting", "q1", "planning"],
            "source": "upload",
            "processing_status": "completed"
        }
    ]
    
    for doc_data in sample_docs:
        doc = Document(**doc_data)
        db.add(doc)
    
    db.commit()
    print(f"✓ Created {len(sample_docs)} sample documents")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_categories(db)
        seed_sample_documents(db)
        print("✓ Database seeded successfully")
    finally:
        db.close()
```

---

## EXECUTION INSTRUCTIONS FOR AI ASSISTANT

### Step 1: Create Project Structure
1. Create all directories listed in PROJECT STRUCTURE
2. Create `__init__.py` files in all Python packages
3. Copy the provided model files to their locations

### Step 2: Setup Database
1. Run `scripts/init_db.py` to create database and schema
2. Verify all tables exist: `psql -d doc_intelligence -c "\dt"`

### Step 3: Create CRUD Layer
1. Create `app/crud/` directory
2. Implement `document.py` with all CRUD operations
3. Create similar CRUD for categories

### Step 4: Create API Layer
1. Implement all schemas in `app/schemas/`
2. Create API endpoints in `app/api/v1/`
3. Setup dependencies in `app/api/deps.py`

### Step 5: Setup Main Application
1. Create `app/main.py` with FastAPI app
2. Configure CORS
3. Include all routers

### Step 6: Testing
1. Run: `python scripts/init_db.py`
2. Run: `python scripts/seed_data.py`
3. Start server: `uvicorn app.main:app --reload`
4. Test endpoints: `http://localhost:8000/docs`

### Step 7: Verify Success
- [ ] Database created with all tables
- [ ] Can create documents via API
- [ ] Can retrieve documents
- [ ] Can update documents
- [ ] Can search documents
- [ ] Categories work correctly

---

## TESTING CHECKLIST

Test these via the auto-generated Swagger docs at `http://localhost:8000/docs`:

1. **GET /api/v1/documents** - Should return empty array or seeded docs
2. **POST /api/v1/documents/upload** - Upload a test file
3. **GET /api/v1/documents/{id}** - Get document details
4. **PUT /api/v1/documents/{id}** - Update user tags
5. **POST /api/v1/documents/search** - Search by keyword
6. **GET /api/v1/categories** - List all categories

---

## COMMON ISSUES & SOLUTIONS

**Issue**: Database connection fails
**Solution**: Check DATABASE_URL in .env matches your PostgreSQL setup

**Issue**: Import errors with models
**Solution**: Ensure all `__init__.py` files exist and export correctly

**Issue**: Alembic migrations fail
**Solution**: Make sure schema.sql ran successfully first

---

## NEXT SPRINT PREVIEW

After Sprint 1 is complete, we'll move to **Sprint 2: Document Processing Pipeline** which will add:
- File upload handling
- Text extraction from PDFs, DOCX, images
- Thumbnail generation
- File storage system

---

## SUCCESS CRITERIA

✅ PostgreSQL database running with all tables
✅ SQLAlchemy models working with relationships
✅ FastAPI server starts without errors
✅ Can perform all CRUD operations via API
✅ Full-text search returns results
✅ Swagger docs accessible and functional
✅ Seed data loads successfully

When all criteria are met, Sprint 1 is COMPLETE! 🎉
