# SPRINT 3: AI ANALYSIS INTEGRATION - CURSOR/WINDSURF PROMPT

## SPRINT OVERVIEW

**Sprint 3 Goal**: Integrate Anthropic Claude API to automatically analyze documents, generate summaries, extract key points, identify entities, detect action items, and suggest categories.

**Duration**: 2 weeks  
**Prerequisites**: Sprint 1 & 2 completed (database working, documents uploading and processing)

---

## WHAT YOU'RE BUILDING

An intelligent document analysis system powered by Claude that:
1. Generates concise 3-5 sentence summaries
2. Extracts key points and main ideas
3. Identifies entities (people, organizations, dates, locations)
4. Detects action items and tasks
5. Suggests appropriate categories
6. Assigns confidence scores
7. Discovers new categories from document patterns

---

## FILES TO CREATE

```
backend/
├── app/
│   ├── services/
│   │   ├── ai_analyzer.py              [MAIN - Claude API integration]
│   │   ├── summarizer.py               [Document summarization]
│   │   ├── categorizer.py              [Auto-categorization]
│   │   ├── entity_extractor.py         [Entity recognition]
│   │   └── category_discovery.py       [NEW - discover categories]
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── document_analysis.py        [Analysis prompts]
│   │   ├── summarization.py            [Summarization prompts]
│   │   └── category_discovery.py       [Category discovery prompts]
│   │
│   ├── api/v1/
│   │   └── analysis.py                 [Analysis endpoints - NEW]
│   │
│   └── config.py                        [UPDATE - add AI settings]
│
├── tests/
│   └── test_services/
│       ├── test_ai_analyzer.py
│       ├── test_summarizer.py
│       └── test_categorizer.py
│
├── .env.example                         [UPDATE - add Anthropic key]
└── requirements.txt                     [UPDATE - add anthropic]
```

---

## TASK 1: UPDATE REQUIREMENTS & CONFIG

### Update requirements.txt

```txt
# Existing dependencies from Sprint 1 & 2...

# AI Integration
anthropic==0.18.1              # Claude API client
tiktoken==0.6.0                # Token counting
```

**Install command**:
```bash
pip install anthropic==0.18.1 tiktoken==0.6.0
```

### Update .env.example

```bash
# Existing environment variables...

# AI Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
AI_MODEL=claude-3-5-sonnet-20241022
AI_MAX_TOKENS=4096
AI_TEMPERATURE=0.7

# Feature Flags
ENABLE_AUTO_CATEGORIZATION=true
ENABLE_ENTITY_EXTRACTION=true
ENABLE_ACTION_ITEM_DETECTION=true
CATEGORY_CONFIDENCE_THRESHOLD=0.7
```

### Update app/config.py

```python
# app/config.py - ADD THESE SETTINGS

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Existing settings...
    
    # AI Settings
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "claude-3-5-sonnet-20241022")
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "4096"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    
    # Feature flags
    ENABLE_AUTO_CATEGORIZATION: bool = os.getenv("ENABLE_AUTO_CATEGORIZATION", "true").lower() == "true"
    ENABLE_ENTITY_EXTRACTION: bool = os.getenv("ENABLE_ENTITY_EXTRACTION", "true").lower() == "true"
    ENABLE_ACTION_ITEM_DETECTION: bool = os.getenv("ENABLE_ACTION_ITEM_DETECTION", "true").lower() == "true"
    CATEGORY_CONFIDENCE_THRESHOLD: float = float(os.getenv("CATEGORY_CONFIDENCE_THRESHOLD", "0.7"))
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## TASK 2: CREATE PROMPT TEMPLATES

```python
# app/prompts/document_analysis.py

"""
Prompt templates for document analysis
"""

def get_analysis_prompt(text: str, filename: str, existing_categories: list[str]) -> str:
    """
    Generate comprehensive document analysis prompt
    """
    
    # Truncate text if too long (keep first 8000 characters for context)
    text_sample = text[:8000] if len(text) > 8000 else text
    
    categories_text = ', '.join(existing_categories) if existing_categories else 'None yet - suggest appropriate categories'
    
    return f"""Analyze this document and provide structured insights.

FILENAME: {filename}

DOCUMENT CONTENT:
{text_sample}

EXISTING CATEGORIES:
{categories_text}

Provide a JSON response with this exact structure:
{{
  "summary": "A concise 3-5 sentence summary of the document. Focus on the main purpose, key information, and important conclusions.",
  
  "document_type": "report|note|article|reference|receipt|form|letter|email|presentation|spreadsheet|other",
  
  "key_points": [
    "Most important point or finding from the document",
    "Second most important point",
    "Third most important point",
    "Additional key points as needed (3-7 total)"
  ],
  
  "entities": {{
    "people": ["Names of people mentioned"],
    "organizations": ["Companies, institutions, groups"],
    "dates": ["Important dates in YYYY-MM-DD format when possible"],
    "locations": ["Places, addresses, cities, countries"]
  }},
  
  "action_items": [
    {{
      "text": "Description of the action item or task",
      "assignee": "Person responsible (if mentioned, else null)",
      "due_date": "YYYY-MM-DD format (if mentioned, else null)",
      "priority": "high|medium|low"
    }}
  ],
  
  "suggested_category": "Most appropriate category name from existing list OR new category if needed",
  "category_confidence": 0.85,
  "create_new_category": false,
  "new_category_description": "Only if create_new_category is true - explain what this category should contain",
  
  "tags": ["relevant", "searchable", "keywords", "from document"],
  
  "sentiment": "positive|negative|neutral|mixed",
  
  "topics": ["main", "subject", "areas", "covered"],
  
  "language": "en"
}}

IMPORTANT INSTRUCTIONS:
- Be concise and accurate
- Only suggest creating a new category if the content is clearly distinct from existing categories (confidence threshold: 80%)
- Extract only explicit action items mentioned in the document - don't infer tasks
- For dates, convert to YYYY-MM-DD format when possible
- Use confidence score honestly (0.0-1.0) - don't artificially inflate
- Keep key points to 3-7 items, prioritize by importance
- Return ONLY valid JSON, no markdown formatting, no additional text
- If a field has no data, use appropriate empty value ([], {{}}, null, "")
"""


def get_quick_summary_prompt(text: str) -> str:
    """
    Quick summarization prompt for when we just need a summary
    """
    text_sample = text[:8000] if len(text) > 8000 else text
    
    return f"""Provide a concise 3-5 sentence summary of this document.

Focus on:
- Main purpose or topic
- Key information or findings
- Important conclusions or recommendations

DOCUMENT:
{text_sample}

Return ONLY the summary text, no additional formatting or explanation.
"""
```

```python
# app/prompts/category_discovery.py

"""
Prompts for discovering categories from document corpus
"""

def get_category_discovery_prompt(document_summaries: list[dict]) -> str:
    """
    Analyze multiple documents to suggest natural category structure
    """
    
    # Format document summaries
    docs_text = "\n\n".join([
        f"Document {i+1}: {doc['filename']}\n{doc['summary']}"
        for i, doc in enumerate(document_summaries[:50])  # Limit to 50 docs
    ])
    
    return f"""Based on these document summaries, suggest 5-10 natural categories that would organize them effectively.

DOCUMENTS:
{docs_text}

Suggest categories that:
1. Reflect actual content patterns in the documents
2. Are mutually exclusive where possible (minimize overlap)
3. Have clear, user-friendly names (2-3 words max)
4. Will scale as more documents are added
5. Avoid being too granular (e.g., use "Emails" not "Work Emails" and "Personal Emails")
6. Cover the major themes present in the document corpus

Return JSON array:
[
  {{
    "name": "Category Name",
    "description": "What types of documents belong in this category",
    "color": "#3B82F6",
    "icon": "💼",
    "example_documents": ["doc1.pdf", "doc2.docx"]
  }}
]

Return ONLY valid JSON, no additional text or markdown formatting.
"""
```

```python
# app/prompts/summarization.py

"""
Specialized summarization prompts
"""

def get_email_summary_prompt(text: str) -> str:
    """Summarization prompt optimized for emails"""
    return f"""Summarize this email in 2-3 sentences.

Include:
- Main purpose (request, update, notification, etc.)
- Key information or action needed
- Important context

EMAIL:
{text[:4000]}

Return only the summary, no additional text.
"""


def get_technical_doc_summary_prompt(text: str) -> str:
    """Summarization prompt optimized for technical documents"""
    return f"""Summarize this technical document in 3-4 sentences.

Include:
- Main topic or technology
- Key findings or recommendations
- Important technical details or specifications

DOCUMENT:
{text[:6000]}

Return only the summary, no additional text.
"""
```

---

## TASK 3: CREATE AI ANALYZER SERVICE

```python
# app/services/ai_analyzer.py

"""
AI Analyzer Service
Main interface to Anthropic Claude API
"""

from anthropic import Anthropic
import json
import logging
from typing import Dict, List, Optional

from app.config import settings
from app.prompts.document_analysis import get_analysis_prompt, get_quick_summary_prompt

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """
    Claude-powered document analysis
    """
    
    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not set - AI features will be disabled")
            self.client = None
        else:
            self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE
    
    def analyze_document(
        self,
        text: str,
        filename: str,
        existing_categories: List[str]
    ) -> Optional[Dict]:
        """
        Comprehensive document analysis
        
        Returns:
        {
            'summary': str,
            'document_type': str,
            'key_points': list,
            'entities': dict,
            'action_items': list,
            'suggested_category': str,
            'category_confidence': float,
            'create_new_category': bool,
            'tags': list,
            'sentiment': str,
            'topics': list,
            'language': str
        }
        """
        
        if not self.client:
            logger.error("AI analysis called but API key not configured")
            return None
        
        try:
            # Build prompt
            prompt = get_analysis_prompt(text, filename, existing_categories)
            
            logger.info(f"Analyzing document: {filename}")
            
            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Extract response text
            response_text = message.content[0].text
            
            # Parse JSON response
            analysis = self._parse_json_response(response_text)
            
            logger.info(f"Analysis completed for {filename}")
            logger.debug(f"Suggested category: {analysis.get('suggested_category')} (confidence: {analysis.get('category_confidence')})")
            
            return analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return None
    
    def quick_summarize(self, text: str) -> Optional[str]:
        """
        Quick summarization without full analysis
        """
        
        if not self.client:
            return None
        
        try:
            prompt = get_quick_summary_prompt(text)
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return message.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Quick summarization failed: {e}")
            return None
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON from Claude's response
        Handles cases where Claude wraps JSON in markdown code blocks
        """
        
        # Remove markdown code block formatting if present
        cleaned = response_text.strip()
        
        if cleaned.startswith("```json"):
            cleaned = cleaned.split("```json")[1]
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        
        cleaned = cleaned.strip()
        
        # Parse JSON
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text}")
            
            # Return minimal valid structure
            return {
                'summary': response_text[:500],
                'key_points': [],
                'entities': {},
                'action_items': [],
                'suggested_category': 'Uncategorized',
                'category_confidence': 0.0,
                'tags': [],
                'sentiment': 'neutral',
                'topics': [],
                'language': 'en'
            }


# Singleton instance
ai_analyzer = AIAnalyzer()
```

---

## TASK 4: CREATE CATEGORIZER SERVICE

```python
# app/services/categorizer.py

"""
Categorizer Service
Handles document categorization logic
"""

from sqlalchemy.orm import Session
from typing import Dict, Optional
import logging

from app.models.category import Category
from app.models.document import Document
from app.config import settings

logger = logging.getLogger(__name__)


class Categorizer:
    """
    Manage document categorization
    """
    
    def apply_category(
        self,
        db: Session,
        document: Document,
        analysis: Dict
    ) -> Optional[Category]:
        """
        Apply category to document based on AI analysis
        
        Returns the category that was applied
        """
        
        if not settings.ENABLE_AUTO_CATEGORIZATION:
            logger.info("Auto-categorization disabled")
            return None
        
        suggested_category = analysis.get('suggested_category')
        confidence = analysis.get('category_confidence', 0.0)
        create_new = analysis.get('create_new_category', False)
        
        # Check confidence threshold
        if confidence < settings.CATEGORY_CONFIDENCE_THRESHOLD:
            logger.info(f"Category confidence {confidence} below threshold {settings.CATEGORY_CONFIDENCE_THRESHOLD}")
            return self._get_uncategorized(db)
        
        # Find or create category
        if create_new:
            category = self._create_category(
                db,
                name=suggested_category,
                description=analysis.get('new_category_description', ''),
                ai_generated=True
            )
        else:
            category = self._find_category(db, suggested_category)
            
            if not category:
                # Fallback to uncategorized
                logger.warning(f"Suggested category '{suggested_category}' not found")
                category = self._get_uncategorized(db)
        
        # Apply to document
        document.ai_category_id = category.id
        document.ai_confidence = confidence
        
        logger.info(f"Applied category '{category.name}' to document {document.id}")
        
        return category
    
    def _find_category(self, db: Session, name: str) -> Optional[Category]:
        """Find category by name (case-insensitive)"""
        return db.query(Category).filter(
            Category.name.ilike(name)
        ).first()
    
    def _create_category(
        self,
        db: Session,
        name: str,
        description: str,
        ai_generated: bool = True
    ) -> Category:
        """Create new category"""
        
        # Generate slug
        slug = Category.generate_slug(name)
        
        # Check if already exists
        existing = db.query(Category).filter(Category.slug == slug).first()
        if existing:
            return existing
        
        # Assign color (rotate through preset colors)
        colors = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#F97316', '#06B6D4']
        color_index = db.query(Category).count() % len(colors)
        
        category = Category(
            name=name,
            slug=slug,
            description=description,
            color=colors[color_index],
            ai_generated=ai_generated,
            created_by_user=False
        )
        
        db.add(category)
        db.commit()
        db.refresh(category)
        
        logger.info(f"Created new category: {name}")
        
        return category
    
    def _get_uncategorized(self, db: Session) -> Category:
        """Get or create 'Uncategorized' category"""
        uncategorized = db.query(Category).filter(
            Category.slug == 'uncategorized'
        ).first()
        
        if not uncategorized:
            uncategorized = Category(
                name='Uncategorized',
                slug='uncategorized',
                description='Documents not yet categorized',
                color='#6B7280',
                icon='📄',
                ai_generated=False,
                created_by_user=False
            )
            db.add(uncategorized)
            db.commit()
            db.refresh(uncategorized)
        
        return uncategorized


# Singleton instance
categorizer = Categorizer()
```

---

## TASK 5: CREATE CATEGORY DISCOVERY SERVICE

```python
# app/services/category_discovery.py

"""
Category Discovery Service
Analyzes document corpus to suggest natural categories
"""

from sqlalchemy.orm import Session
from typing import List, Dict
import logging

from app.models.document import Document
from app.models.category import Category
from app.services.ai_analyzer import ai_analyzer
from app.prompts.category_discovery import get_category_discovery_prompt

logger = logging.getLogger(__name__)


class CategoryDiscovery:
    """
    Discover natural categories from document corpus
    """
    
    MIN_DOCUMENTS = 10  # Minimum docs needed for discovery
    
    def discover_categories(self, db: Session) -> List[Category]:
        """
        Analyze existing documents and suggest category structure
        
        Best run when:
        - First 10-20 documents uploaded
        - Periodically (e.g., every 100 new docs)
        - User requests category optimization
        """
        
        # Get documents with summaries
        documents = db.query(Document).filter(
            Document.summary.isnot(None),
            Document.processing_status == 'completed'
        ).limit(50).all()
        
        if len(documents) < self.MIN_DOCUMENTS:
            logger.warning(f"Not enough documents for discovery ({len(documents)} < {self.MIN_DOCUMENTS})")
            return []
        
        # Prepare document summaries
        doc_summaries = [
            {
                'filename': doc.filename,
                'summary': doc.summary
            }
            for doc in documents
        ]
        
        logger.info(f"Discovering categories from {len(doc_summaries)} documents")
        
        # Generate prompt and call AI
        prompt = get_category_discovery_prompt(doc_summaries)
        
        try:
            message = ai_analyzer.client.messages.create(
                model=ai_analyzer.model,
                max_tokens=2000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            suggestions = ai_analyzer._parse_json_response(response_text)
            
            # Create suggested categories
            created_categories = []
            for suggestion in suggestions:
                category = self._create_suggested_category(db, suggestion)
                if category:
                    created_categories.append(category)
            
            logger.info(f"Discovered {len(created_categories)} new categories")
            
            return created_categories
            
        except Exception as e:
            logger.error(f"Category discovery failed: {e}")
            return []
    
    def _create_suggested_category(self, db: Session, suggestion: Dict) -> Category:
        """Create category from AI suggestion"""
        
        name = suggestion.get('name')
        slug = Category.generate_slug(name)
        
        # Check if exists
        existing = db.query(Category).filter(Category.slug == slug).first()
        if existing:
            logger.info(f"Category '{name}' already exists")
            return None
        
        category = Category(
            name=name,
            slug=slug,
            description=suggestion.get('description', ''),
            color=suggestion.get('color', '#3B82F6'),
            icon=suggestion.get('icon'),
            ai_generated=True,
            created_by_user=False
        )
        
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return category


# Singleton instance
category_discovery = CategoryDiscovery()
```

---

## TASK 6: UPDATE DOCUMENT PROCESSOR TO USE AI

```python
# app/services/document_processor.py - UPDATE process_upload method

# Add this import at the top
from app.services.ai_analyzer import ai_analyzer
from app.services.categorizer import categorizer

# Update the process_upload method - add AI analysis after text extraction:

async def process_upload(
    self,
    db: Session,
    file: UploadFile,
    source: str = "upload"
) -> Document:
    """
    Process uploaded file through complete pipeline
    
    Steps:
    1. Validate file
    2. Save to storage
    3. Create document record
    4. Extract text
    5. Generate thumbnail
    6. AI ANALYSIS (NEW)
    7. Update document record
    """
    
    # ... existing code through text extraction ...
    
    # NEW: Step 6 - AI Analysis
    if document.raw_text:
        logger.info(f"Starting AI analysis for {document.id}")
        
        # Get existing categories
        categories = db.query(Category).all()
        category_names = [c.name for c in categories]
        
        # Analyze document
        analysis = ai_analyzer.analyze_document(
            text=document.raw_text,
            filename=document.filename,
            existing_categories=category_names
        )
        
        if analysis:
            # Update document with analysis results
            document.summary = analysis.get('summary')
            document.key_points = analysis.get('key_points', [])
            document.entities = analysis.get('entities', {})
            document.action_items = analysis.get('action_items', [])
            document.ai_tags = analysis.get('tags', [])
            
            # Apply category
            categorizer.apply_category(db, document, analysis)
            
            logger.info("AI analysis completed successfully")
        else:
            logger.warning("AI analysis returned None")
    
    # ... rest of existing code ...
```

---

## TASK 7: CREATE ANALYSIS API ENDPOINTS

```python
# app/api/v1/analysis.py

"""
Analysis API Endpoints
Manual triggering and category discovery
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.api.deps import get_db
from app.models.document import Document
from app.models.category import Category
from app.crud.document import document_crud
from app.services.ai_analyzer import ai_analyzer
from app.services.categorizer import categorizer
from app.services.category_discovery import category_discovery
from app.schemas.category import CategoryResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/documents/{document_id}/analyze")
async def reanalyze_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Manually trigger AI analysis for a document
    Useful for:
    - Re-analyzing after category changes
    - Fixing failed analysis
    - Getting updated analysis with new prompt
    """
    
    document = document_crud.get(db, id=document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not document.raw_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no text content to analyze"
        )
    
    # Get categories
    categories = db.query(Category).all()
    category_names = [c.name for c in categories]
    
    # Analyze
    analysis = ai_analyzer.analyze_document(
        text=document.raw_text,
        filename=document.filename,
        existing_categories=category_names
    )
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI analysis failed"
        )
    
    # Update document
    document.summary = analysis.get('summary')
    document.key_points = analysis.get('key_points', [])
    document.entities = analysis.get('entities', {})
    document.action_items = analysis.get('action_items', [])
    document.ai_tags = analysis.get('tags', [])
    
    # Apply category
    categorizer.apply_category(db, document, analysis)
    
    db.commit()
    db.refresh(document)
    
    return {
        "message": "Document re-analyzed successfully",
        "document_id": str(document.id),
        "summary": document.summary,
        "category": document.ai_category.name if document.ai_category else None,
        "confidence": document.ai_confidence
    }


@router.post("/categories/discover", response_model=List[CategoryResponse])
async def discover_categories(
    db: Session = Depends(get_db)
):
    """
    Analyze document corpus and discover natural categories
    
    Best used when:
    - First 10-20 documents uploaded
    - Every 100 new documents
    - User wants to optimize categories
    """
    
    discovered = category_discovery.discover_categories(db)
    
    return discovered


@router.get("/stats")
async def get_analysis_stats(
    db: Session = Depends(get_db)
):
    """
    Get statistics about AI analysis coverage
    """
    
    total_docs = db.query(Document).count()
    analyzed_docs = db.query(Document).filter(
        Document.summary.isnot(None)
    ).count()
    categorized_docs = db.query(Document).filter(
        Document.ai_category_id.isnot(None)
    ).count()
    
    return {
        "total_documents": total_docs,
        "analyzed_documents": analyzed_docs,
        "categorized_documents": categorized_docs,
        "analysis_coverage": round(analyzed_docs / total_docs * 100, 1) if total_docs > 0 else 0,
        "categorization_coverage": round(categorized_docs / total_docs * 100, 1) if total_docs > 0 else 0
    }
```

---

## TASK 8: UPDATE MAIN APP

```python
# app/main.py - ADD THIS

from app.api.v1 import analysis

# Add to router includes
app.include_router(analysis.router, prefix="/api/v1")
```

---

## TASK 9: CREATE TESTS

```python
# tests/test_services/test_ai_analyzer.py

"""
Test AI Analyzer Service
"""

import pytest
from app.services.ai_analyzer import ai_analyzer


class TestAIAnalyzer:
    """Test AI analysis functionality"""
    
    @pytest.mark.skipif(not ai_analyzer.client, reason="API key not configured")
    def test_analyze_document(self):
        """Test full document analysis"""
        
        sample_text = """
        Meeting Notes - Q1 Planning
        Date: January 15, 2026
        
        Discussed launch strategy for new product line.
        
        Key Decisions:
        - Budget approved: $150K
        - Target market: 25-40 age demographic
        - Marketing channels: Social media, content marketing, events
        
        Action Items:
        - John: Prepare market analysis by Jan 30
        - Sarah: Draft marketing plan by Feb 5
        - Team: Review positioning statement by Jan 25
        """
        
        result = ai_analyzer.analyze_document(
            text=sample_text,
            filename="meeting-notes.txt",
            existing_categories=["Work", "Personal", "Finance"]
        )
        
        assert result is not None
        assert 'summary' in result
        assert 'key_points' in result
        assert len(result['key_points']) > 0
        assert 'entities' in result
        assert 'action_items' in result
        assert 'suggested_category' in result
        assert 'category_confidence' in result
    
    @pytest.mark.skipif(not ai_analyzer.client, reason="API key not configured")
    def test_quick_summarize(self):
        """Test quick summarization"""
        
        text = "This is a test document about project management."
        
        summary = ai_analyzer.quick_summarize(text)
        
        assert summary is not None
        assert len(summary) > 0
        assert isinstance(summary, str)
```

---

## EXECUTION INSTRUCTIONS

### Step 1: Get Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys
4. Create a new key
5. Copy to your `.env` file:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Step 2: Install Dependencies

```bash
pip install anthropic==0.18.1 tiktoken==0.6.0
```

### Step 3: Implement AI Services

1. Create `app/prompts/` directory with all prompt templates
2. Create `app/services/ai_analyzer.py` - Main AI service
3. Create `app/services/categorizer.py` - Categorization logic
4. Create `app/services/category_discovery.py` - Category discovery
5. Update `app/services/document_processor.py` - Add AI analysis step

### Step 4: Create API Endpoints

1. Create `app/api/v1/analysis.py` - Analysis endpoints
2. Update `app/main.py` to include analysis router

### Step 5: Update Configuration

1. Update `app/config.py` with AI settings
2. Update `.env` with Anthropic API key

### Step 6: Test AI Integration

```bash
# Start server
uvicorn app.main:app --reload

# Upload a document
curl -X POST "http://localhost:8000/api/v1/upload/" \
  -F "file=@test-document.pdf"

# Check if it was analyzed
# Look for summary, key_points, entities in response

# Test manual analysis
curl -X POST "http://localhost:8000/api/v1/analysis/documents/{doc_id}/analyze"

# Discover categories
curl -X POST "http://localhost:8000/api/v1/analysis/categories/discover"
```

---

## TESTING CHECKLIST

Test via Swagger UI at `http://localhost:8000/docs`:

### Automatic Analysis (on upload)
- [ ] Upload PDF → Summary generated
- [ ] Upload Word doc → Key points extracted
- [ ] Document auto-categorized with confidence score
- [ ] Entities extracted (people, dates, organizations)
- [ ] Action items detected from text
- [ ] Tags assigned automatically

### Manual Analysis
- [ ] POST `/api/v1/analysis/documents/{id}/analyze` works
- [ ] Can re-analyze documents
- [ ] Analysis updates existing data

### Category Discovery
- [ ] POST `/api/v1/analysis/categories/discover` works
- [ ] New categories created from document patterns
- [ ] Categories have descriptions and icons

### Analysis Quality
- [ ] Summaries are concise (3-5 sentences)
- [ ] Key points capture main ideas
- [ ] Entities are accurate
- [ ] Categories make sense
- [ ] Confidence scores are reasonable

### Error Handling
- [ ] Works without API key (analysis skipped)
- [ ] Handles documents with no text
- [ ] Handles API errors gracefully
- [ ] Malformed JSON responses handled

---

## COMMON ISSUES & SOLUTIONS

**Issue**: "API key not configured"
**Solution**: Add `ANTHROPIC_API_KEY=sk-ant-...` to `.env` file

**Issue**: Analysis returns None
**Solution**: Check API key is valid, check network connectivity, check logs

**Issue**: JSON parsing fails
**Solution**: Update `_parse_json_response` to handle Claude's response format

**Issue**: Categories not being assigned
**Solution**: Check `CATEGORY_CONFIDENCE_THRESHOLD` - might be too high

**Issue**: Out of API credits
**Solution**: Add credits at https://console.anthropic.com/settings/billing

**Issue**: Slow analysis
**Solution**: Reduce `AI_MAX_TOKENS` or truncate text more aggressively

---

## SUCCESS CRITERIA

✅ Documents automatically analyzed on upload  
✅ Summaries generated (3-5 sentences)  
✅ Key points extracted (3-7 items)  
✅ Entities identified (people, dates, orgs, locations)  
✅ Action items detected  
✅ Documents auto-categorized  
✅ Confidence scores assigned  
✅ New categories suggested when appropriate  
✅ Category discovery works on corpus  
✅ Manual re-analysis endpoint works  
✅ All tests pass  

**When all criteria met, Sprint 3 is COMPLETE!** 🎉

---

## USAGE EXAMPLES

### After Sprint 3 Completion

```bash
# Upload a meeting notes document
curl -X POST "http://localhost:8000/api/v1/upload/" \
  -F "file=@meeting-notes.pdf"

# Response includes AI analysis:
{
  "id": "uuid",
  "filename": "meeting-notes.pdf",
  "summary": "Q1 planning meeting discussing product launch strategy...",
  "key_points": [
    "Budget approved at $150K",
    "Target market: 25-40 demographic",
    "Launch planned for March 2026"
  ],
  "entities": {
    "people": ["John Smith", "Sarah Johnson"],
    "dates": ["2026-01-30", "2026-03-15"],
    "organizations": ["Marketing Team"]
  },
  "action_items": [
    {
      "text": "Prepare market analysis",
      "assignee": "John",
      "due_date": "2026-01-30"
    }
  ],
  "ai_category": {
    "name": "Work",
    "confidence": 0.92
  }
}
```

---

## NEXT SPRINT PREVIEW

**Sprint 4: Background Processing & Queue** will add:
- Celery/RQ task queue
- Asynchronous document processing
- Retry logic for failed tasks
- WebSocket for real-time status updates
- Processing dashboard

Your AI analysis will run in the background so uploads return immediately!

---

**Ready to build intelligent document analysis?** 🤖✨
