# PHASE 3: SEARCH & INTELLIGENCE - COMPLETE EXECUTION PROMPT

## OVERVIEW FOR AI CODING ASSISTANT

You are extending the Document Intelligence Platform (Phases 1-2 complete) with advanced search and intelligence features. Users will be able to perform semantic search, discover document relationships, view timeline visualizations, and get AI-generated insights.

This prompt covers **all 4 sprints of Phase 3** (8 weeks of work). Implement them in order for best results.

---

## PREREQUISITES

✅ **Phase 1 must be complete:**
- Database and models working
- Document processing functional
- AI analysis integrated
- Background queue operational

✅ **Phase 2 should be complete (or in progress):**
- Cloud integrations syncing documents
- Large document corpus available (100+ docs recommended)

✅ **New requirements:**
- Vector database (Qdrant or ChromaDB)
- Additional Python libraries for embeddings and visualization

---

# SPRINT 9: FULL-TEXT SEARCH

## Objective
Implement robust full-text search with PostgreSQL, including filters, highlighting, and suggestions.

## Tasks

### 1. Update requirements.txt

Add:
```txt
# Search enhancements
sqlalchemy-utils==0.41.1
unidecode==1.3.8
```

Install:
```bash
pip install sqlalchemy-utils unidecode
```

### 2. Enhance search service

```python
# app/services/search_service.py

from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import logging

from app.models.document import Document
from app.models.category import Category

logger = logging.getLogger(__name__)


class SearchService:
    """
    Advanced full-text search with filters and ranking
    """
    
    def search_documents(
        self,
        db: Session,
        query: str,
        filters: Optional[Dict] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict:
        """
        Search documents with full-text search and filters
        
        Args:
            query: Search query text
            filters: {
                'categories': [uuid, ...],
                'sources': ['upload', 'gmail', ...],
                'date_range': {'start': date, 'end': date},
                'tags': ['tag1', 'tag2'],
                'is_favorite': bool
            }
        
        Returns:
            {
                'results': [...],
                'total': int,
                'query': str,
                'filters': {...}
            }
        """
        
        # Base query with full-text search
        search_query = db.query(Document).filter(
            Document.is_archived == False
        )
        
        # Apply full-text search
        if query:
            search_query = search_query.filter(
                func.to_tsvector('english', Document.search_vector).match(
                    func.plainto_tsquery('english', query)
                )
            )
        
        # Apply filters
        if filters:
            search_query = self._apply_filters(search_query, filters)
        
        # Get total count
        total = search_query.count()
        
        # Order by relevance
        if query:
            search_query = search_query.order_by(
                func.ts_rank(
                    Document.search_vector,
                    func.plainto_tsquery('english', query)
                ).desc()
            )
        else:
            search_query = search_query.order_by(Document.upload_date.desc())
        
        # Paginate
        results = search_query.offset(skip).limit(limit).all()
        
        # Calculate relevance scores
        results_with_scores = []
        for doc in results:
            score = self._calculate_relevance(doc, query)
            results_with_scores.append({
                'document': doc,
                'relevance': score,
                'highlights': self._generate_highlights(doc, query)
            })
        
        return {
            'results': results_with_scores,
            'total': total,
            'query': query,
            'filters': filters,
            'page': skip // limit + 1,
            'pages': (total + limit - 1) // limit
        }
    
    def _apply_filters(self, query, filters: Dict):
        """Apply search filters"""
        
        if filters.get('categories'):
            query = query.filter(
                or_(
                    Document.ai_category_id.in_(filters['categories']),
                    Document.user_category_id.in_(filters['categories'])
                )
            )
        
        if filters.get('sources'):
            query = query.filter(Document.source.in_(filters['sources']))
        
        if filters.get('date_range'):
            if filters['date_range'].get('start'):
                query = query.filter(
                    Document.upload_date >= filters['date_range']['start']
                )
            if filters['date_range'].get('end'):
                query = query.filter(
                    Document.upload_date <= filters['date_range']['end']
                )
        
        if filters.get('tags'):
            # Search in both AI and user tags
            for tag in filters['tags']:
                query = query.filter(
                    or_(
                        Document.ai_tags.contains([tag]),
                        Document.user_tags.contains([tag])
                    )
                )
        
        if filters.get('is_favorite') is not None:
            query = query.filter(Document.is_favorite == filters['is_favorite'])
        
        if filters.get('file_types'):
            query = query.filter(Document.file_type.in_(filters['file_types']))
        
        return query
    
    def _calculate_relevance(self, document: Document, query: str) -> float:
        """Calculate relevance score (0.0 - 1.0)"""
        
        if not query:
            return 1.0
        
        query_lower = query.lower()
        score = 0.0
        
        # Check filename match (highest weight)
        if query_lower in document.filename.lower():
            score += 0.3
        
        # Check summary match
        if document.summary and query_lower in document.summary.lower():
            score += 0.25
        
        # Check tags match
        all_tags = (document.ai_tags or []) + (document.user_tags or [])
        if any(query_lower in tag.lower() for tag in all_tags):
            score += 0.2
        
        # Check category match
        if document.ai_category and query_lower in document.ai_category.name.lower():
            score += 0.15
        
        # Check entities match
        if document.entities:
            for entity_type, entities in document.entities.items():
                if any(query_lower in str(e).lower() for e in entities):
                    score += 0.1
                    break
        
        return min(score, 1.0)
    
    def _generate_highlights(self, document: Document, query: str) -> List[str]:
        """Generate text highlights for search results"""
        
        if not query:
            return []
        
        highlights = []
        query_lower = query.lower()
        
        # Highlight from summary
        if document.summary and query_lower in document.summary.lower():
            # Find context around match
            idx = document.summary.lower().find(query_lower)
            start = max(0, idx - 50)
            end = min(len(document.summary), idx + len(query) + 50)
            highlight = document.summary[start:end]
            if start > 0:
                highlight = "..." + highlight
            if end < len(document.summary):
                highlight = highlight + "..."
            highlights.append(highlight)
        
        # Highlight from text
        if document.raw_text and query_lower in document.raw_text.lower():
            idx = document.raw_text.lower().find(query_lower)
            start = max(0, idx - 100)
            end = min(len(document.raw_text), idx + len(query) + 100)
            highlight = document.raw_text[start:end]
            if start > 0:
                highlight = "..." + highlight
            if end < len(document.raw_text):
                highlight = highlight + "..."
            highlights.append(highlight)
        
        return highlights[:3]  # Max 3 highlights
    
    def get_search_suggestions(self, db: Session, partial_query: str, limit: int = 5) -> List[str]:
        """
        Get search suggestions based on partial query
        """
        
        suggestions = set()
        
        # Suggest from category names
        categories = db.query(Category).filter(
            Category.name.ilike(f'%{partial_query}%')
        ).limit(limit).all()
        
        for cat in categories:
            suggestions.add(cat.name)
        
        # Suggest from tags
        docs_with_tags = db.query(Document.ai_tags, Document.user_tags).filter(
            or_(
                func.array_to_string(Document.ai_tags, ' ').ilike(f'%{partial_query}%'),
                func.array_to_string(Document.user_tags, ' ').ilike(f'%{partial_query}%')
            )
        ).limit(limit * 2).all()
        
        for ai_tags, user_tags in docs_with_tags:
            for tag in (ai_tags or []) + (user_tags or []):
                if partial_query.lower() in tag.lower():
                    suggestions.add(tag)
        
        return sorted(list(suggestions))[:limit]
    
    def get_popular_searches(self, db: Session, limit: int = 10) -> List[Dict]:
        """
        Get popular search terms (would need search_logs table to track)
        For now, return popular tags and categories
        """
        
        # Most used categories
        popular_categories = db.query(
            Category.name,
            Category.document_count
        ).filter(
            Category.document_count > 0
        ).order_by(
            Category.document_count.desc()
        ).limit(limit).all()
        
        return [
            {'term': name, 'count': count}
            for name, count in popular_categories
        ]


# Singleton instance
search_service = SearchService()
```

### 3. Create advanced search API

```python
# app/api/v1/search.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.api.deps import get_db
from app.services.search_service import search_service
from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def search_documents(
    query: str = Query(..., min_length=2, description="Search query"),
    categories: Optional[List[str]] = Query(None),
    sources: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    file_types: Optional[List[str]] = Query(None),
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    is_favorite: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Advanced document search with filters
    
    Example:
    POST /search?query=meeting&categories=work&date_start=2026-01-01
    """
    
    # Build filters
    filters = {}
    
    if categories:
        filters['categories'] = categories
    
    if sources:
        filters['sources'] = sources
    
    if tags:
        filters['tags'] = tags
    
    if file_types:
        filters['file_types'] = file_types
    
    if date_start or date_end:
        filters['date_range'] = {
            'start': date_start,
            'end': date_end
        }
    
    if is_favorite is not None:
        filters['is_favorite'] = is_favorite
    
    # Perform search
    results = search_service.search_documents(
        db=db,
        query=query,
        filters=filters,
        skip=skip,
        limit=limit
    )
    
    return results


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """Get search suggestions as user types"""
    
    suggestions = search_service.get_search_suggestions(db, q, limit)
    
    return {
        'query': q,
        'suggestions': suggestions
    }


@router.get("/popular")
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get popular/trending search terms"""
    
    popular = search_service.get_popular_searches(db, limit)
    
    return {
        'popular_searches': popular
    }


@router.get("/facets")
async def get_search_facets(
    query: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get search facets (available filters with counts)
    Useful for building filter UI
    """
    
    # Base query
    base_query = db.query(Document).filter(Document.is_archived == False)
    
    if query:
        base_query = base_query.filter(
            func.to_tsvector('english', Document.search_vector).match(
                func.plainto_tsquery('english', query)
            )
        )
    
    # Get category counts
    category_facets = db.query(
        Category.id,
        Category.name,
        func.count(Document.id).label('count')
    ).join(
        Document,
        or_(
            Document.ai_category_id == Category.id,
            Document.user_category_id == Category.id
        )
    ).group_by(Category.id, Category.name).all()
    
    # Get source counts
    source_facets = base_query.with_entities(
        Document.source,
        func.count(Document.id).label('count')
    ).group_by(Document.source).all()
    
    # Get file type counts
    file_type_facets = base_query.with_entities(
        Document.file_type,
        func.count(Document.id).label('count')
    ).group_by(Document.file_type).all()
    
    return {
        'categories': [
            {'id': str(id), 'name': name, 'count': count}
            for id, name, count in category_facets
        ],
        'sources': [
            {'source': source, 'count': count}
            for source, count in source_facets
        ],
        'file_types': [
            {'type': ftype, 'count': count}
            for ftype, count in file_type_facets
        ]
    }
```

### 4. Create search schemas

```python
# app/schemas/search.py

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID

class SearchFilters(BaseModel):
    categories: Optional[List[UUID]] = None
    sources: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    date_range: Optional[Dict[str, date]] = None
    is_favorite: Optional[bool] = None

class SearchRequest(BaseModel):
    query: str
    filters: Optional[SearchFilters] = None
    skip: int = 0
    limit: int = 50

class SearchResultItem(BaseModel):
    document: Dict[str, Any]
    relevance: float
    highlights: List[str]

class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    total: int
    query: str
    filters: Optional[Dict] = None
    page: int
    pages: int
```

### 5. Update main app

```python
# app/main.py - ADD THIS

from app.api.v1 import search

app.include_router(search.router, prefix="/api/v1")
```

### 6. Test Sprint 9

```bash
# Basic search
curl -X POST "http://localhost:8000/api/v1/search/?query=meeting"

# Search with filters
curl -X POST "http://localhost:8000/api/v1/search/?query=project&sources=gmail&date_start=2026-01-01"

# Get suggestions
curl "http://localhost:8000/api/v1/search/suggestions?q=mee"

# Get facets (for filter UI)
curl "http://localhost:8000/api/v1/search/facets"

# Popular searches
curl "http://localhost:8000/api/v1/search/popular"
```

✅ **Sprint 9 Complete when:**
- Full-text search works
- Filters work (categories, sources, dates, tags)
- Search suggestions appear as typing
- Highlights show context
- Relevance scoring works
- Pagination works
- Facets API returns filter options

---

# SPRINT 10: SEMANTIC SEARCH & EMBEDDINGS

## Objective
Add vector embeddings and semantic search using Qdrant/ChromaDB for meaning-based search.

## Tasks

### 1. Update requirements.txt

Add:
```txt
# Vector Search
qdrant-client==1.7.3
sentence-transformers==2.5.1
```

Install:
```bash
pip install qdrant-client sentence-transformers
```

### 2. Start Qdrant (Vector Database)

```bash
# Using Docker
docker run -d -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage \
    qdrant/qdrant

# Or add to docker-compose.yml:
```

```yaml
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
```

### 3. Create embedding service

```python
# app/services/embedding_service.py

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging
from typing import List, Dict
import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Generate and manage document embeddings
    """
    
    def __init__(self):
        # Load embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dimensions
        self.embedding_dim = 384
        
        # Connect to Qdrant
        self.qdrant = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        
        self.collection_name = "documents"
        
        # Create collection if doesn't exist
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        
        try:
            self.qdrant.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists")
        except:
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection '{self.collection_name}'")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Text to embed
        
        Returns:
            384-dimensional vector
        """
        
        if not text:
            return [0.0] * self.embedding_dim
        
        # Truncate long text
        text = text[:5000]
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)
        
        return embedding.tolist()
    
    def store_document_embedding(
        self,
        document_id: str,
        text: str,
        metadata: Dict = None
    ):
        """
        Generate and store document embedding
        
        Args:
            document_id: UUID of document
            text: Document text to embed
            metadata: Additional metadata to store
        """
        
        # Generate embedding
        embedding = self.generate_embedding(text)
        
        # Prepare point
        point = PointStruct(
            id=document_id,
            vector=embedding,
            payload=metadata or {}
        )
        
        # Upload to Qdrant
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        logger.info(f"Stored embedding for document {document_id}")
    
    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.5
    ) -> List[Dict]:
        """
        Perform semantic search
        
        Args:
            query: Search query
            limit: Max results
            score_threshold: Minimum similarity score (0-1)
        
        Returns:
            List of {document_id, score, ...}
        """
        
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        
        # Search in Qdrant
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'document_id': result.id,
                'score': result.score,
                'metadata': result.payload
            })
        
        return formatted_results
    
    def find_similar_documents(
        self,
        document_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find documents similar to given document
        """
        
        # Get document embedding
        try:
            doc_vector = self.qdrant.retrieve(
                collection_name=self.collection_name,
                ids=[document_id]
            )[0].vector
        except:
            logger.error(f"Document {document_id} not found in vector DB")
            return []
        
        # Search for similar
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=doc_vector,
            limit=limit + 1  # +1 because it will include itself
        )
        
        # Filter out the document itself
        formatted_results = []
        for result in results:
            if result.id != document_id:
                formatted_results.append({
                    'document_id': result.id,
                    'score': result.score,
                    'metadata': result.payload
                })
        
        return formatted_results[:limit]
    
    def delete_document_embedding(self, document_id: str):
        """Delete document embedding from vector DB"""
        
        self.qdrant.delete(
            collection_name=self.collection_name,
            points_selector=[document_id]
        )
        
        logger.info(f"Deleted embedding for document {document_id}")


# Singleton instance
embedding_service = EmbeddingService()
```

### 4. Create background task for embeddings

```python
# Add to app/workers/tasks.py

@celery_app.task(base=DatabaseTask, bind=True)
def embed_document_task(self, document_id: str):
    """
    Generate and store document embedding
    """
    
    from app.services.embedding_service import embedding_service
    
    document = self.db.query(Document).filter(
        Document.id == document_id
    ).first()
    
    if not document:
        logger.error(f"Document {document_id} not found")
        return
    
    # Combine text for embedding
    text_to_embed = f"{document.filename} {document.summary or ''} {document.raw_text or ''}"
    
    # Prepare metadata
    metadata = {
        'filename': document.filename,
        'category': document.ai_category.name if document.ai_category else None,
        'tags': (document.ai_tags or []) + (document.user_tags or []),
        'upload_date': document.upload_date.isoformat() if document.upload_date else None
    }
    
    # Generate and store embedding
    embedding_service.store_document_embedding(
        document_id=str(document.id),
        text=text_to_embed,
        metadata=metadata
    )
    
    logger.info(f"Embedded document {document_id}")
```

### 5. Update document processing to generate embeddings

```python
# In app/workers/tasks.py analyze_document_task

# After AI analysis completes, add:

# Queue embedding generation
embed_document_task.delay(document_id)
```

### 6. Create semantic search API

```python
# Add to app/api/v1/search.py

@router.post("/semantic")
async def semantic_search(
    query: str = Query(..., min_length=3),
    limit: int = Query(10, ge=1, le=50),
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """
    Semantic search using vector embeddings
    
    Finds documents by meaning, not just keywords
    """
    
    from app.services.embedding_service import embedding_service
    
    # Perform semantic search
    vector_results = embedding_service.semantic_search(
        query=query,
        limit=limit,
        score_threshold=threshold
    )
    
    # Get full document details
    document_ids = [r['document_id'] for r in vector_results]
    documents = db.query(Document).filter(
        Document.id.in_(document_ids)
    ).all()
    
    # Build results with scores
    results = []
    for vec_result in vector_results:
        doc = next((d for d in documents if str(d.id) == vec_result['document_id']), None)
        if doc:
            results.append({
                'document': doc.to_dict(),
                'similarity_score': vec_result['score'],
                'metadata': vec_result['metadata']
            })
    
    return {
        'query': query,
        'results': results,
        'total': len(results)
    }


@router.get("/documents/{document_id}/similar")
async def find_similar_documents(
    document_id: UUID,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Find documents similar to the given document
    """
    
    from app.services.embedding_service import embedding_service
    
    # Check document exists
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Find similar
    similar = embedding_service.find_similar_documents(
        document_id=str(document_id),
        limit=limit
    )
    
    # Get full documents
    doc_ids = [s['document_id'] for s in similar]
    documents = db.query(Document).filter(
        Document.id.in_(doc_ids)
    ).all()
    
    # Build results
    results = []
    for sim in similar:
        doc = next((d for d in documents if str(d.id) == sim['document_id']), None)
        if doc:
            results.append({
                'document': doc.to_dict(),
                'similarity_score': sim['score']
            })
    
    return {
        'document_id': str(document_id),
        'similar_documents': results
    }
```

### 7. Create batch embedding script

```python
# scripts/generate_embeddings.py

"""
Generate embeddings for all existing documents
Run once after installing Sprint 10
"""

from app.db.base import SessionLocal
from app.models.document import Document
from app.workers.tasks import embed_document_task

def generate_all_embeddings():
    db = SessionLocal()
    
    # Get all documents
    documents = db.query(Document).filter(
        Document.processing_status == 'completed'
    ).all()
    
    print(f"Found {len(documents)} documents to embed")
    
    # Queue embedding tasks
    for doc in documents:
        embed_document_task.delay(str(doc.id))
        print(f"Queued: {doc.filename}")
    
    print(f"Queued {len(documents)} embedding tasks")
    db.close()

if __name__ == "__main__":
    generate_all_embeddings()
```

### 8. Test Sprint 10

```bash
# Generate embeddings for existing docs
python scripts/generate_embeddings.py

# Wait for embeddings to process (check Flower)

# Test semantic search
curl -X POST "http://localhost:8000/api/v1/search/semantic?query=quarterly%20financial%20report"

# Should find documents about finances even if they don't contain exact phrase

# Find similar documents
curl "http://localhost:8000/api/v1/search/documents/{doc_id}/similar"

# Try semantic vs keyword search
curl -X POST "http://localhost:8000/api/v1/search/?query=budget"
curl -X POST "http://localhost:8000/api/v1/search/semantic?query=budget"

# Semantic should find "financial planning", "spending", "costs" etc.
```

✅ **Sprint 10 Complete when:**
- Embeddings generated for all documents
- Semantic search finds relevant docs by meaning
- Similar documents API works
- Can compare keyword vs semantic search results
- Embedding generation integrated into processing pipeline

---

# SPRINT 11: CATEGORY INTELLIGENCE & ANALYTICS

## Objective
Advanced category management with analytics, auto-categorization refinement, and category insights.

## Tasks

### 1. Create category analytics service

```python
# app/services/category_analytics.py

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict
from datetime import datetime, timedelta
import logging

from app.models.document import Document
from app.models.category import Category

logger = logging.getLogger(__name__)


class CategoryAnalytics:
    """
    Category intelligence and analytics
    """
    
    def get_category_stats(self, db: Session, category_id: str) -> Dict:
        """
        Get detailed statistics for a category
        """
        
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return None
        
        # Document count over time
        docs_this_week = db.query(Document).filter(
            Document.ai_category_id == category_id,
            Document.upload_date >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        docs_this_month = db.query(Document).filter(
            Document.ai_category_id == category_id,
            Document.upload_date >= datetime.utcnow() - timedelta(days=30)
        ).count()
        
        # Average confidence
        avg_confidence = db.query(func.avg(Document.ai_confidence)).filter(
            Document.ai_category_id == category_id
        ).scalar() or 0.0
        
        # Top tags in this category
        all_docs = db.query(Document.ai_tags).filter(
            Document.ai_category_id == category_id
        ).all()
        
        tag_counts = {}
        for (tags,) in all_docs:
            for tag in (tags or []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # File type distribution
        file_types = db.query(
            Document.file_type,
            func.count(Document.id).label('count')
        ).filter(
            Document.ai_category_id == category_id
        ).group_by(Document.file_type).all()
        
        # Source distribution
        sources = db.query(
            Document.source,
            func.count(Document.id).label('count')
        ).filter(
            Document.ai_category_id == category_id
        ).group_by(Document.source).all()
        
        return {
            'category': {
                'id': str(category.id),
                'name': category.name,
                'description': category.description,
                'color': category.color
            },
            'total_documents': category.document_count,
            'new_this_week': docs_this_week,
            'new_this_month': docs_this_month,
            'avg_confidence': round(avg_confidence, 2),
            'top_tags': [{'tag': tag, 'count': count} for tag, count in top_tags],
            'file_types': [{'type': ft, 'count': count} for ft, count in file_types],
            'sources': [{'source': src, 'count': count} for src, count in sources]
        }
    
    def suggest_category_merges(self, db: Session, similarity_threshold: float = 0.7) -> List[Dict]:
        """
        Suggest categories that might be merged
        Based on semantic similarity of documents in categories
        """
        
        from app.services.embedding_service import embedding_service
        
        categories = db.query(Category).filter(
            Category.document_count > 3  # Only categories with enough docs
        ).all()
        
        suggestions = []
        
        # Compare each pair of categories
        for i, cat1 in enumerate(categories):
            for cat2 in categories[i+1:]:
                # Get sample documents from each category
                docs1 = db.query(Document).filter(
                    Document.ai_category_id == cat1.id
                ).limit(10).all()
                
                docs2 = db.query(Document).filter(
                    Document.ai_category_id == cat2.id
                ).limit(10).all()
                
                # Calculate average similarity
                # (Simplified - in production, use embeddings)
                
                # Check tag overlap
                tags1 = set()
                tags2 = set()
                
                for doc in docs1:
                    tags1.update(doc.ai_tags or [])
                
                for doc in docs2:
                    tags2.update(doc.ai_tags or [])
                
                if tags1 and tags2:
                    overlap = len(tags1 & tags2) / len(tags1 | tags2)
                    
                    if overlap > similarity_threshold:
                        suggestions.append({
                            'category1': {'id': str(cat1.id), 'name': cat1.name},
                            'category2': {'id': str(cat2.id), 'name': cat2.name},
                            'similarity': round(overlap, 2),
                            'reason': f"{len(tags1 & tags2)} common tags"
                        })
        
        return suggestions
    
    def optimize_categories(self, db: Session) -> Dict:
        """
        Analyze and suggest category optimizations
        """
        
        all_categories = db.query(Category).all()
        
        issues = []
        
        # Find empty categories
        empty = [c for c in all_categories if c.document_count == 0]
        if empty:
            issues.append({
                'type': 'empty_categories',
                'count': len(empty),
                'categories': [{'id': str(c.id), 'name': c.name} for c in empty],
                'suggestion': 'Delete these categories'
            })
        
        # Find categories with very few documents
        sparse = [c for c in all_categories if 0 < c.document_count < 3]
        if sparse:
            issues.append({
                'type': 'sparse_categories',
                'count': len(sparse),
                'categories': [{'id': str(c.id), 'name': c.name, 'count': c.document_count} for c in sparse],
                'suggestion': 'Consider merging with related categories'
            })
        
        # Find categories with very many documents (might need splitting)
        large = [c for c in all_categories if c.document_count > 100]
        if large:
            issues.append({
                'type': 'large_categories',
                'count': len(large),
                'categories': [{'id': str(c.id), 'name': c.name, 'count': c.document_count} for c in large],
                'suggestion': 'Consider splitting into subcategories'
            })
        
        return {
            'total_categories': len(all_categories),
            'issues': issues,
            'health_score': self._calculate_health_score(all_categories)
        }
    
    def _calculate_health_score(self, categories: List[Category]) -> float:
        """
        Calculate category system health (0-100)
        """
        
        if not categories:
            return 0.0
        
        score = 100.0
        
        # Penalize empty categories
        empty_count = sum(1 for c in categories if c.document_count == 0)
        score -= (empty_count / len(categories)) * 20
        
        # Penalize very imbalanced distribution
        counts = [c.document_count for c in categories if c.document_count > 0]
        if counts:
            import statistics
            if statistics.stdev(counts) > statistics.mean(counts) * 2:
                score -= 15
        
        # Reward good number of categories (5-15 is ideal)
        active_categories = len([c for c in categories if c.document_count > 0])
        if active_categories < 5:
            score -= 10
        elif active_categories > 20:
            score -= 15
        
        return max(0, min(100, score))


# Singleton instance
category_analytics = CategoryAnalytics()
```

### 2. Create category analytics API

```python
# app/api/v1/category_analytics.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db
from app.services.category_analytics import category_analytics

router = APIRouter(prefix="/categories", tags=["category-analytics"])


@router.get("/{category_id}/stats")
async def get_category_statistics(
    category_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get detailed statistics for a category
    """
    
    stats = category_analytics.get_category_stats(db, str(category_id))
    
    if not stats:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return stats


@router.get("/analytics/merge-suggestions")
async def get_merge_suggestions(
    similarity_threshold: float = 0.7,
    db: Session = Depends(get_db)
):
    """
    Get suggestions for categories that could be merged
    """
    
    suggestions = category_analytics.suggest_category_merges(
        db,
        similarity_threshold=similarity_threshold
    )
    
    return {
        'suggestions': suggestions,
        'count': len(suggestions)
    }


@router.get("/analytics/optimization")
async def get_category_optimization(
    db: Session = Depends(get_db)
):
    """
    Analyze category system and suggest optimizations
    """
    
    analysis = category_analytics.optimize_categories(db)
    
    return analysis


@router.post("/{category_id}/merge/{target_category_id}")
async def merge_categories(
    category_id: UUID,
    target_category_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Merge source category into target category
    """
    
    from app.models.category import Category
    from app.models.document import Document
    
    source = db.query(Category).filter(Category.id == category_id).first()
    target = db.query(Category).filter(Category.id == target_category_id).first()
    
    if not source or not target:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Move all documents to target category
    docs = db.query(Document).filter(
        or_(
            Document.ai_category_id == category_id,
            Document.user_category_id == category_id
        )
    ).all()
    
    for doc in docs:
        if doc.ai_category_id == category_id:
            doc.ai_category_id = target_category_id
        if doc.user_category_id == category_id:
            doc.user_category_id = target_category_id
    
    # Delete source category
    db.delete(source)
    db.commit()
    
    return {
        'message': f'Merged {source.name} into {target.name}',
        'documents_moved': len(docs),
        'target_category': target.to_dict()
    }
```

### 3. Test Sprint 11

```bash
# Get category stats
curl "http://localhost:8000/api/v1/categories/{id}/stats"

# Get merge suggestions
curl "http://localhost:8000/api/v1/categories/analytics/merge-suggestions"

# Get optimization analysis
curl "http://localhost:8000/api/v1/categories/analytics/optimization"

# Merge categories
curl -X POST "http://localhost:8000/api/v1/categories/{source_id}/merge/{target_id}"
```

✅ **Sprint 11 Complete when:**
- Category stats API works
- Shows document count, trends, top tags
- Merge suggestions based on similarity
- Optimization analysis provides actionable insights
- Can merge categories via API

---

# SPRINT 12: DOCUMENT RELATIONSHIPS & INSIGHTS

## Objective
Auto-detect document relationships, generate timeline, and create insights dashboard.

## Tasks

### 1. Create relationship detection service

```python
# app/services/relationship_detector.py

from sqlalchemy.orm import Session
from typing import List, Dict
import logging

from app.models.document import Document
from app.models.relationships import DocumentRelationship
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class RelationshipDetector:
    """
    Detect and create relationships between documents
    """
    
    def detect_relationships(self, db: Session, document_id: str):
        """
        Detect all relationships for a document
        """
        
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return
        
        # Find similar documents (semantic similarity)
        similar_docs = embedding_service.find_similar_documents(
            document_id=document_id,
            limit=10
        )
        
        for similar in similar_docs:
            if similar['score'] > 0.8:  # High similarity
                self._create_relationship(
                    db,
                    document_id,
                    similar['document_id'],
                    'similar_to',
                    similar['score']
                )
        
        # Find references (documents with same entities)
        if document.entities:
            self._find_entity_references(db, document)
        
        # Find follow-ups (same thread/category, later date)
        if document.extracted_metadata.get('thread_id'):
            self._find_thread_followups(db, document)
    
    def _create_relationship(
        self,
        db: Session,
        source_id: str,
        target_id: str,
        rel_type: str,
        confidence: float
    ):
        """Create relationship if doesn't exist"""
        
        existing = db.query(DocumentRelationship).filter(
            DocumentRelationship.source_doc_id == source_id,
            DocumentRelationship.target_doc_id == target_id,
            DocumentRelationship.relationship_type == rel_type
        ).first()
        
        if not existing:
            relationship = DocumentRelationship(
                source_doc_id=source_id,
                target_doc_id=target_id,
                relationship_type=rel_type,
                confidence=confidence
            )
            db.add(relationship)
            db.commit()
            logger.info(f"Created {rel_type} relationship: {source_id} -> {target_id}")
    
    def _find_entity_references(self, db: Session, document: Document):
        """Find documents that share entities"""
        
        if not document.entities:
            return
        
        # Extract people and organizations
        people = document.entities.get('people', [])
        orgs = document.entities.get('organizations', [])
        
        if not people and not orgs:
            return
        
        # Find other documents with same entities
        all_docs = db.query(Document).filter(
            Document.id != document.id,
            Document.entities.isnot(None)
        ).limit(100).all()
        
        for other_doc in all_docs:
            other_people = other_doc.entities.get('people', [])
            other_orgs = other_doc.entities.get('organizations', [])
            
            # Check overlap
            people_overlap = len(set(people) & set(other_people))
            org_overlap = len(set(orgs) & set(other_orgs))
            
            if people_overlap >= 2 or org_overlap >= 1:
                confidence = min(1.0, (people_overlap + org_overlap) / 5)
                self._create_relationship(
                    db,
                    str(document.id),
                    str(other_doc.id),
                    'references',
                    confidence
                )
    
    def _find_thread_followups(self, db: Session, document: Document):
        """Find follow-up documents in same email thread"""
        
        thread_id = document.extracted_metadata.get('thread_id')
        if not thread_id:
            return
        
        # Find other docs in same thread
        thread_docs = db.query(Document).filter(
            Document.id != document.id,
            Document.extracted_metadata['thread_id'].astext == thread_id,
            Document.upload_date > document.upload_date
        ).all()
        
        for follow_up in thread_docs:
            self._create_relationship(
                db,
                str(document.id),
                str(follow_up.id),
                'follows_up',
                0.9
            )


# Singleton instance
relationship_detector = RelationshipDetector()
```

### 2. Create insights generator

```python
# app/services/insights_generator.py

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict
from datetime import datetime, timedelta
import logging

from app.models.document import Document
from app.models.category import Category

logger = logging.getLogger(__name__)


class InsightsGenerator:
    """
    Generate insights and trends from document corpus
    """
    
    def generate_daily_insights(self, db: Session) -> Dict:
        """
        Generate insights for today
        """
        
        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        
        # Documents uploaded today
        docs_today = db.query(Document).filter(
            func.date(Document.upload_date) == today
        ).count()
        
        docs_yesterday = db.query(Document).filter(
            func.date(Document.upload_date) == yesterday
        ).count()
        
        # Action items today
        action_items = []
        recent_docs = db.query(Document).filter(
            Document.upload_date >= datetime.utcnow() - timedelta(days=7),
            Document.action_items.isnot(None)
        ).all()
        
        for doc in recent_docs:
            for item in (doc.action_items or []):
                if not item.get('completed', False):
                    action_items.append({
                        'text': item.get('text'),
                        'document': doc.filename,
                        'due_date': item.get('due_date'),
                        'priority': item.get('priority', 'medium')
                    })
        
        # Most active category
        active_category = db.query(
            Category.name,
            func.count(Document.id).label('count')
        ).join(
            Document,
            Document.ai_category_id == Category.id
        ).filter(
            func.date(Document.upload_date) == today
        ).group_by(Category.name).order_by(desc('count')).first()
        
        return {
            'date': str(today),
            'documents_today': docs_today,
            'documents_yesterday': docs_yesterday,
            'change': docs_today - docs_yesterday,
            'action_items': sorted(action_items, key=lambda x: x.get('priority') == 'high', reverse=True)[:10],
            'most_active_category': active_category[0] if active_category else None,
            'summary': f"Added {docs_today} documents today" + (f", {len(action_items)} pending action items" if action_items else "")
        }
    
    def generate_weekly_trends(self, db: Session) -> Dict:
        """
        Generate trends for past week
        """
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        # Documents by day
        daily_counts = db.query(
            func.date(Document.upload_date).label('date'),
            func.count(Document.id).label('count')
        ).filter(
            Document.upload_date >= week_ago
        ).group_by(func.date(Document.upload_date)).all()
        
        # Top categories this week
        top_categories = db.query(
            Category.name,
            func.count(Document.id).label('count')
        ).join(
            Document,
            Document.ai_category_id == Category.id
        ).filter(
            Document.upload_date >= week_ago
        ).group_by(Category.name).order_by(desc('count')).limit(5).all()
        
        # Top sources
        top_sources = db.query(
            Document.source,
            func.count(Document.id).label('count')
        ).filter(
            Document.upload_date >= week_ago
        ).group_by(Document.source).all()
        
        # Trending tags
        all_tags = db.query(Document.ai_tags, Document.user_tags).filter(
            Document.upload_date >= week_ago
        ).all()
        
        tag_counts = {}
        for ai_tags, user_tags in all_tags:
            for tag in (ai_tags or []) + (user_tags or []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        trending_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'period': 'Last 7 days',
            'daily_activity': [{'date': str(date), 'count': count} for date, count in daily_counts],
            'top_categories': [{'category': name, 'count': count} for name, count in top_categories],
            'sources': [{'source': source, 'count': count} for source, count in top_sources],
            'trending_tags': [{'tag': tag, 'count': count} for tag, count in trending_tags]
        }
    
    def find_document_clusters(self, db: Session, limit: int = 5) -> List[Dict]:
        """
        Find clusters of related documents
        """
        
        # Get most connected documents
        from app.models.relationships import DocumentRelationship
        
        most_connected = db.query(
            DocumentRelationship.source_doc_id,
            func.count(DocumentRelationship.id).label('connection_count')
        ).group_by(
            DocumentRelationship.source_doc_id
        ).order_by(
            desc('connection_count')
        ).limit(limit).all()
        
        clusters = []
        for doc_id, count in most_connected:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                related = db.query(DocumentRelationship).filter(
                    DocumentRelationship.source_doc_id == doc_id
                ).all()
                
                clusters.append({
                    'center_document': {
                        'id': str(doc.id),
                        'filename': doc.filename,
                        'summary': doc.summary
                    },
                    'connections': count,
                    'related_documents': [
                        {
                            'id': str(rel.target_doc_id),
                            'type': rel.relationship_type,
                            'confidence': rel.confidence
                        }
                        for rel in related
                    ]
                })
        
        return clusters


# Singleton instance
insights_generator = InsightsGenerator()
```

### 3. Create insights API

```python
# app/api/v1/insights.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from app.api.deps import get_db
from app.services.insights_generator import insights_generator
from app.services.relationship_detector import relationship_detector

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/daily")
async def get_daily_insights(db: Session = Depends(get_db)):
    """Get insights for today"""
    
    insights = insights_generator.generate_daily_insights(db)
    return insights


@router.get("/weekly")
async def get_weekly_trends(db: Session = Depends(get_db)):
    """Get trends for past week"""
    
    trends = insights_generator.generate_weekly_trends(db)
    return trends


@router.get("/clusters")
async def get_document_clusters(
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Find clusters of related documents"""
    
    clusters = insights_generator.find_document_clusters(db, limit)
    return {'clusters': clusters}


@router.post("/documents/{document_id}/relationships")
async def detect_document_relationships(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Detect and create relationships for a document"""
    
    relationship_detector.detect_relationships(db, document_id)
    
    return {'message': 'Relationships detected', 'document_id': document_id}
```

### 4. Add relationship detection to processing

```python
# Add to app/workers/tasks.py

# In analyze_document_task, after completion:

# Detect relationships
from app.workers.tasks import detect_relationships_task
detect_relationships_task.delay(document_id)


@celery_app.task(base=DatabaseTask, bind=True)
def detect_relationships_task(self, document_id: str):
    """Background task to detect document relationships"""
    
    from app.services.relationship_detector import relationship_detector
    
    relationship_detector.detect_relationships(self.db, document_id)
```

### 5. Test Sprint 12

```bash
# Get daily insights
curl "http://localhost:8000/api/v1/insights/daily"

# Get weekly trends
curl "http://localhost:8000/api/v1/insights/weekly"

# Get document clusters
curl "http://localhost:8000/api/v1/insights/clusters"

# Manually trigger relationship detection
curl -X POST "http://localhost:8000/api/v1/insights/documents/{id}/relationships"

# Check document relationships
curl "http://localhost:8000/api/v1/documents/{id}"
# Should include related_documents in response
```

✅ **Sprint 12 Complete when:**
- Daily insights show today's activity
- Weekly trends show patterns
- Document clusters identified
- Relationships auto-detected
- Action items extracted and prioritized
- Can see related documents for any doc

---

# PHASE 3 VERIFICATION

## Complete Testing Flow

```bash
# 1. Full-text search
curl -X POST "http://localhost:8000/api/v1/search/?query=meeting&sources=gmail"

# 2. Semantic search
curl -X POST "http://localhost:8000/api/v1/search/semantic?query=financial%20planning"

# Should find budget docs, spending reports, etc.

# 3. Find similar documents
curl "http://localhost:8000/api/v1/search/documents/{id}/similar"

# 4. Category analytics
curl "http://localhost:8000/api/v1/categories/{id}/stats"

# 5. Category optimization
curl "http://localhost:8000/api/v1/categories/analytics/optimization"

# 6. Daily insights
curl "http://localhost:8000/api/v1/insights/daily"

# Should show:
# - Documents added today
# - Pending action items
# - Most active category

# 7. Weekly trends
curl "http://localhost:8000/api/v1/insights/weekly"

# Should show:
# - Daily activity chart
# - Top categories
# - Trending tags

# 8. Document clusters
curl "http://localhost:8000/api/v1/insights/clusters"

# Should show groups of related docs

# 9. Search suggestions
curl "http://localhost:8000/api/v1/search/suggestions?q=mee"

# Should suggest: "meeting", "meetings", etc.

# 10. Compare search types
curl -X POST "http://localhost:8000/api/v1/search/?query=budget" > keyword.json
curl -X POST "http://localhost:8000/api/v1/search/semantic?query=budget" > semantic.json

# Semantic should find more related docs
```

## Success Criteria

✅ **Full-Text Search**
- Keyword search works
- Filters work (categories, dates, sources, tags)
- Search suggestions appear
- Highlights show context
- Pagination works

✅ **Semantic Search**
- Finds documents by meaning
- Works better than keyword for concepts
- Similar documents API accurate
- Embeddings generated for all docs

✅ **Category Intelligence**
- Stats show trends and insights
- Merge suggestions make sense
- Optimization provides actionable advice
- Can merge categories successfully

✅ **Document Relationships**
- Similar docs detected automatically
- Entity-based references found
- Email threads linked
- Clusters identified

✅ **Insights Dashboard**
- Daily insights show recent activity
- Weekly trends visualize patterns
- Action items prioritized
- Data accurate and useful

---

# DEPLOYMENT NOTES

## Qdrant Setup

For production:
```yaml
# docker-compose.yml
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
  volumes:
    - qdrant_data:/qdrant/storage
  environment:
    - QDRANT__SERVICE__GRPC_PORT=6334
```

## Embedding Model

The `all-MiniLM-L6-v2` model:
- Fast and lightweight
- 384 dimensions
- Good for most use cases

For better quality (slower):
- `all-mpnet-base-v2` (768 dim)
- `multi-qa-mpnet-base-dot-v1` (768 dim)

## Background Tasks

Add to Celery beat schedule:
```python
'detect-relationships': {
    'task': 'app.workers.tasks.detect_all_relationships',
    'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
},
```

---

# TROUBLESHOOTING

**Qdrant connection fails**
```bash
# Check Qdrant is running
curl http://localhost:6333/health

# Restart Qdrant
docker restart qdrant
```

**Embeddings slow**
```bash
# Use GPU if available
pip install sentence-transformers[cuda]

# Or batch process
python scripts/generate_embeddings.py --batch-size 100
```

**Search returns no results**
```bash
# Check search_vector is populated
SELECT COUNT(*) FROM documents WHERE search_vector IS NOT NULL;

# Regenerate if needed
UPDATE documents SET search_vector = to_tsvector('english', coalesce(filename,'') || ' ' || coalesce(summary,''));
```

**Insights API slow**
```bash
# Add indexes if missing
CREATE INDEX idx_documents_upload_date_date ON documents(DATE(upload_date));

# Use caching
# Cache insights for 1 hour in Redis
```

---

# NEXT STEPS

After Phase 3 is complete, you have:
- ✅ Complete backend (Phase 1)
- ✅ Cloud integrations (Phase 2)
- ✅ Advanced search & intelligence (Phase 3)

**Move to Phase 4: Frontend**
- React UI with timeline visualization
- Search interface with filters
- Connection management
- Insights dashboard
- Real-time updates

---

# EXECUTION SUMMARY

Phase 3 builds advanced intelligence with:

- ✅ Full-text search with filters
- ✅ Search suggestions and autocomplete
- ✅ Semantic search with embeddings (384-dim vectors)
- ✅ Similar document detection
- ✅ Category analytics and optimization
- ✅ Auto-relationship detection
- ✅ Document clustering
- ✅ Daily insights
- ✅ Weekly trends
- ✅ Action item tracking

**Build time**: 8 weeks (4 sprints × 2 weeks each)
**Lines of code**: ~2,500 lines
**Files created**: ~15 files
**New dependencies**: Qdrant, sentence-transformers

Start with Sprint 9 (full-text search) and work sequentially! 🚀