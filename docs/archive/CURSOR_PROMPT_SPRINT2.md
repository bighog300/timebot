# SPRINT 2: DOCUMENT PROCESSING PIPELINE - CURSOR/WINDSURF PROMPT

## SPRINT OVERVIEW

**Sprint 2 Goal**: Build the complete document processing pipeline that handles file uploads, extracts text from various formats (PDF, DOCX, images), generates thumbnails, and stores files securely.

**Duration**: 2 weeks  
**Prerequisites**: Sprint 1 completed (database and models working)

---

## WHAT YOU'RE BUILDING

A robust document processing system that can:
1. Accept file uploads via multipart/form-data
2. Validate and store files securely
3. Extract text from PDFs, Word docs, Excel, PowerPoint
4. Perform OCR on images and scanned PDFs
5. Generate thumbnails for visual previews
6. Extract metadata (author, creation date, etc.)
7. Queue documents for AI processing

---

## FILES TO CREATE

```
backend/
├── app/
│   ├── services/
│   │   ├── document_processor.py      [MAIN - orchestrates processing]
│   │   ├── text_extractor.py          [Extract text from files]
│   │   ├── thumbnail_generator.py     [Generate previews]
│   │   ├── storage.py                 [File storage management]
│   │   └── metadata_extractor.py      [Extract file metadata]
│   │
│   ├── utils/
│   │   ├── file_utils.py              [File validation, MIME types]
│   │   └── image_utils.py             [Image processing helpers]
│   │
│   ├── api/v1/
│   │   └── upload.py                  [Upload endpoint - NEW]
│   │
│   └── config.py                       [Configuration - UPDATE]
│
├── data/                               [CREATE - file storage]
│   ├── uploads/                        [Original files]
│   ├── processed/                      [Extracted text]
│   │   ├── text/
│   │   └── thumbnails/
│   └── temp/                           [Temporary processing]
│
├── tests/
│   └── test_services/
│       ├── test_document_processor.py
│       ├── test_text_extractor.py
│       └── test_storage.py
│
└── requirements.txt                    [UPDATE with new dependencies]
```

---

## TASK 1: UPDATE REQUIREMENTS.TXT

Add these dependencies for document processing:

```txt
# Existing dependencies from Sprint 1...

# Document Processing
pypdf2==3.0.1                 # PDF text extraction
python-docx==1.1.0            # Word document processing
openpyxl==3.1.2               # Excel files
python-pptx==0.6.23           # PowerPoint files
pillow==10.2.0                # Image processing
pytesseract==0.3.10           # OCR
pdf2image==1.17.0             # Convert PDF to images for OCR
python-magic==0.4.27          # MIME type detection

# File handling
aiofiles==23.2.1              # Async file operations
python-multipart==0.0.6       # Multipart form data

# Image processing
reportlab==4.0.9              # PDF generation (for thumbnails)
```

**Install command**:
```bash
pip install pypdf2 python-docx openpyxl python-pptx pillow pytesseract pdf2image python-magic aiofiles python-multipart reportlab
```

**System dependencies** (install via apt/brew):
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils libmagic1

# macOS
brew install tesseract poppler libmagic
```

---

## TASK 2: CREATE FILE STORAGE SERVICE

```python
# app/services/storage.py

"""
File Storage Service
Handles secure file storage and retrieval
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
import hashlib
import aiofiles
from fastapi import UploadFile

class StorageService:
    """Manage file storage on disk"""
    
    def __init__(self):
        # Base directories
        self.base_path = Path(os.getenv("STORAGE_PATH", "/app/data"))
        self.uploads_path = self.base_path / "uploads"
        self.processed_path = self.base_path / "processed"
        self.thumbnails_path = self.processed_path / "thumbnails"
        self.text_path = self.processed_path / "text"
        self.temp_path = self.base_path / "temp"
        
        # Create directories
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create all necessary directories"""
        for path in [
            self.uploads_path,
            self.processed_path,
            self.thumbnails_path,
            self.text_path,
            self.temp_path
        ]:
            path.mkdir(parents=True, exist_ok=True)
    
    def _generate_file_path(self, filename: str, folder: Path) -> Path:
        """
        Generate organized file path with date-based structure
        Example: uploads/2026/04/19/filename.pdf
        """
        now = datetime.now()
        date_path = folder / str(now.year) / f"{now.month:02d}" / f"{now.day:02d}"
        date_path.mkdir(parents=True, exist_ok=True)
        
        # Add hash to prevent collisions
        file_hash = hashlib.md5(f"{filename}{now.isoformat()}".encode()).hexdigest()[:8]
        name, ext = os.path.splitext(filename)
        safe_filename = f"{name}_{file_hash}{ext}"
        
        return date_path / safe_filename
    
    async def save_upload(self, file: UploadFile) -> tuple[Path, int]:
        """
        Save uploaded file
        Returns: (file_path, file_size)
        """
        file_path = self._generate_file_path(file.filename, self.uploads_path)
        
        # Save file
        file_size = 0
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):  # 8KB chunks
                await f.write(chunk)
                file_size += len(chunk)
        
        return file_path, file_size
    
    def save_text(self, document_id: str, text: str) -> Path:
        """Save extracted text"""
        text_file = self.text_path / f"{document_id}.txt"
        text_file.write_text(text, encoding='utf-8')
        return text_file
    
    def save_thumbnail(self, document_id: str, image_bytes: bytes, format: str = "png") -> Path:
        """Save thumbnail image"""
        thumb_file = self.thumbnails_path / f"{document_id}.{format}"
        thumb_file.write_bytes(image_bytes)
        return thumb_file
    
    def get_upload_path(self, original_path: str) -> Optional[Path]:
        """Get path to uploaded file"""
        path = Path(original_path)
        return path if path.exists() else None
    
    def get_thumbnail_path(self, document_id: str) -> Optional[Path]:
        """Get path to thumbnail"""
        for ext in ['png', 'jpg', 'jpeg']:
            thumb_file = self.thumbnails_path / f"{document_id}.{ext}"
            if thumb_file.exists():
                return thumb_file
        return None
    
    def delete_file(self, file_path: Path):
        """Delete a file"""
        if file_path.exists():
            file_path.unlink()
    
    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes"""
        return file_path.stat().st_size if file_path.exists() else 0


# Singleton instance
storage = StorageService()
```

---

## TASK 3: CREATE TEXT EXTRACTION SERVICE

```python
# app/services/text_extractor.py

"""
Text Extraction Service
Extract text from various document formats
"""

from pathlib import Path
from typing import Dict, Any, Optional
import pypdf2
from docx import Document as DocxDocument
import openpyxl
from pptx import Presentation
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import magic
import logging

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extract text from different file types"""
    
    # Supported MIME types
    SUPPORTED_TYPES = {
        'application/pdf': 'extract_pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'extract_docx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'extract_xlsx',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'extract_pptx',
        'text/plain': 'extract_text',
        'image/png': 'extract_image_ocr',
        'image/jpeg': 'extract_image_ocr',
        'image/jpg': 'extract_image_ocr',
        'image/gif': 'extract_image_ocr',
    }
    
    def extract(self, file_path: Path) -> Dict[str, Any]:
        """
        Main extraction method - routes to appropriate extractor
        Returns: {
            'text': str,
            'page_count': int,
            'word_count': int,
            'metadata': dict
        }
        """
        # Detect MIME type
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(str(file_path))
        
        logger.info(f"Extracting text from {file_path.name} (type: {mime_type})")
        
        # Get appropriate extractor
        extractor_method = self.SUPPORTED_TYPES.get(mime_type)
        if not extractor_method:
            raise ValueError(f"Unsupported file type: {mime_type}")
        
        # Call extractor
        extractor = getattr(self, extractor_method)
        result = extractor(file_path)
        
        # Add word count
        result['word_count'] = len(result['text'].split())
        
        return result
    
    def extract_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from PDF"""
        try:
            with open(file_path, 'rb') as f:
                pdf = pypdf2.PdfReader(f)
                
                # Extract text from all pages
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                
                # If no text (scanned PDF), try OCR
                if not text.strip():
                    logger.info("PDF appears to be scanned, attempting OCR...")
                    text = self._ocr_pdf(file_path)
                
                # Get metadata
                metadata = {}
                if pdf.metadata:
                    metadata = {
                        'title': pdf.metadata.get('/Title', ''),
                        'author': pdf.metadata.get('/Author', ''),
                        'subject': pdf.metadata.get('/Subject', ''),
                        'creator': pdf.metadata.get('/Creator', ''),
                    }
                
                return {
                    'text': text,
                    'page_count': len(pdf.pages),
                    'metadata': metadata
                }
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            raise
    
    def _ocr_pdf(self, file_path: Path) -> str:
        """Perform OCR on scanned PDF"""
        try:
            # Convert PDF to images
            images = convert_from_path(str(file_path))
            
            # OCR each page
            text = ""
            for i, image in enumerate(images):
                logger.info(f"OCR processing page {i+1}/{len(images)}")
                page_text = pytesseract.image_to_string(image)
                text += page_text + "\n"
            
            return text
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
    
    def extract_docx(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from Word document"""
        try:
            doc = DocxDocument(str(file_path))
            
            # Extract all paragraphs
            text = "\n".join([para.text for para in doc.paragraphs])
            
            # Get metadata
            metadata = {}
            if hasattr(doc.core_properties, 'author'):
                metadata = {
                    'author': doc.core_properties.author or '',
                    'title': doc.core_properties.title or '',
                    'subject': doc.core_properties.subject or '',
                    'created': str(doc.core_properties.created) if doc.core_properties.created else '',
                }
            
            return {
                'text': text,
                'page_count': 1,  # DOCX doesn't have clear page concept
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"Error extracting DOCX: {e}")
            raise
    
    def extract_xlsx(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from Excel spreadsheet"""
        try:
            wb = openpyxl.load_workbook(str(file_path), data_only=True)
            
            text = ""
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                text += f"\n=== Sheet: {sheet_name} ===\n"
                
                for row in sheet.iter_rows(values_only=True):
                    row_text = " | ".join([str(cell) if cell is not None else "" for cell in row])
                    if row_text.strip():
                        text += row_text + "\n"
            
            return {
                'text': text,
                'page_count': len(wb.sheetnames),
                'metadata': {
                    'sheets': wb.sheetnames,
                    'sheet_count': len(wb.sheetnames)
                }
            }
        except Exception as e:
            logger.error(f"Error extracting XLSX: {e}")
            raise
    
    def extract_pptx(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from PowerPoint presentation"""
        try:
            prs = Presentation(str(file_path))
            
            text = ""
            for i, slide in enumerate(prs.slides):
                text += f"\n=== Slide {i+1} ===\n"
                
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
            
            return {
                'text': text,
                'page_count': len(prs.slides),
                'metadata': {
                    'slide_count': len(prs.slides)
                }
            }
        except Exception as e:
            logger.error(f"Error extracting PPTX: {e}")
            raise
    
    def extract_text(self, file_path: Path) -> Dict[str, Any]:
        """Extract from plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            return {
                'text': text,
                'page_count': 1,
                'metadata': {}
            }
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise
    
    def extract_image_ocr(self, file_path: Path) -> Dict[str, Any]:
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            
            return {
                'text': text,
                'page_count': 1,
                'metadata': {
                    'width': image.width,
                    'height': image.height,
                    'format': image.format
                }
            }
        except Exception as e:
            logger.error(f"Error extracting from image: {e}")
            raise


# Singleton instance
text_extractor = TextExtractor()
```

---

## TASK 4: CREATE THUMBNAIL GENERATOR

```python
# app/services/thumbnail_generator.py

"""
Thumbnail Generator Service
Generate image previews for documents
"""

from pathlib import Path
from typing import Optional
from PIL import Image
from pdf2image import convert_from_path
import io
import logging

logger = logging.getLogger(__name__)


class ThumbnailGenerator:
    """Generate thumbnails for various document types"""
    
    THUMBNAIL_SIZE = (300, 400)  # Width x Height
    QUALITY = 85
    
    def generate(self, file_path: Path, mime_type: str) -> Optional[bytes]:
        """
        Generate thumbnail for file
        Returns: PNG bytes or None if not possible
        """
        try:
            if mime_type == 'application/pdf':
                return self._generate_pdf_thumbnail(file_path)
            elif mime_type.startswith('image/'):
                return self._generate_image_thumbnail(file_path)
            else:
                # For other types, return a generic icon (or None)
                return None
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return None
    
    def _generate_pdf_thumbnail(self, file_path: Path) -> bytes:
        """Generate thumbnail from first page of PDF"""
        # Convert first page to image
        images = convert_from_path(
            str(file_path),
            first_page=1,
            last_page=1,
            dpi=150
        )
        
        if not images:
            raise ValueError("PDF has no pages")
        
        # Resize and convert to bytes
        first_page = images[0]
        first_page.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        
        # Convert to PNG bytes
        img_bytes = io.BytesIO()
        first_page.save(img_bytes, format='PNG', quality=self.QUALITY)
        return img_bytes.getvalue()
    
    def _generate_image_thumbnail(self, file_path: Path) -> bytes:
        """Generate thumbnail from image"""
        image = Image.open(file_path)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize
        image.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG', quality=self.QUALITY)
        return img_bytes.getvalue()


# Singleton instance
thumbnail_generator = ThumbnailGenerator()
```

---

## TASK 5: CREATE DOCUMENT PROCESSOR (ORCHESTRATOR)

```python
# app/services/document_processor.py

"""
Document Processor Service
Main orchestrator for document processing pipeline
"""

from pathlib import Path
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import UploadFile
import logging

from app.models.document import Document
from app.models.processing_queue import ProcessingQueue
from app.services.storage import storage
from app.services.text_extractor import text_extractor
from app.services.thumbnail_generator import thumbnail_generator
import magic

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrate document processing pipeline"""
    
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    ALLOWED_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'text/plain',
        'image/png',
        'image/jpeg',
        'image/jpg',
        'image/gif',
    }
    
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
        6. Update document record
        7. Queue for AI analysis
        """
        
        # Step 1: Validate
        await self._validate_file(file)
        
        # Step 2: Save file
        file_path, file_size = await storage.save_upload(file)
        logger.info(f"Saved file to {file_path}")
        
        # Detect MIME type
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(str(file_path))
        
        # Step 3: Create document record
        document = Document(
            filename=file.filename,
            original_path=str(file_path),
            file_type=Path(file.filename).suffix[1:],  # Remove leading dot
            file_size=file_size,
            mime_type=mime_type,
            source=source,
            processing_status="processing"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        logger.info(f"Created document record: {document.id}")
        
        try:
            # Step 4: Extract text
            extraction_result = text_extractor.extract(file_path)
            
            document.raw_text = extraction_result['text']
            document.page_count = extraction_result['page_count']
            document.word_count = extraction_result['word_count']
            document.extracted_metadata = extraction_result['metadata']
            
            # Save extracted text to file
            storage.save_text(str(document.id), extraction_result['text'])
            
            logger.info(f"Extracted {len(extraction_result['text'])} characters")
            
            # Step 5: Generate thumbnail
            thumbnail_bytes = thumbnail_generator.generate(file_path, mime_type)
            if thumbnail_bytes:
                storage.save_thumbnail(str(document.id), thumbnail_bytes)
                logger.info("Generated thumbnail")
            
            # Step 6: Update status
            document.processing_status = "completed"
            
            # Step 7: Queue for AI analysis
            self._queue_ai_analysis(db, document.id)
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            document.processing_status = "failed"
            document.processing_error = str(e)
        
        db.commit()
        db.refresh(document)
        
        return document
    
    async def _validate_file(self, file: UploadFile):
        """Validate uploaded file"""
        # Check size
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset
        
        if size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Max size: {self.MAX_FILE_SIZE / 1024 / 1024}MB")
        
        # Check type (basic check on filename)
        # More thorough check happens after file is saved
        allowed_extensions = {'.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.png', '.jpg', '.jpeg', '.gif'}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise ValueError(f"File type not allowed: {file_ext}")
    
    def _queue_ai_analysis(self, db: Session, document_id):
        """Queue document for AI analysis"""
        queue_item = ProcessingQueue(
            document_id=document_id,
            task_type="ai_analysis",
            priority=5
        )
        db.add(queue_item)
        logger.info(f"Queued document {document_id} for AI analysis")


# Singleton instance
document_processor = DocumentProcessor()
```

---

## TASK 6: CREATE UPLOAD API ENDPOINT

```python
# app/api/v1/upload.py

"""
File Upload API Endpoint
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.document_processor import document_processor
from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a document for processing
    
    Accepts: PDF, DOCX, XLSX, PPTX, TXT, images (PNG, JPG, GIF)
    Max size: 50MB
    
    Returns: Created document with processing status
    """
    try:
        document = await document_processor.process_upload(db, file)
        return document
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/status/{document_id}")
async def get_processing_status(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get processing status of uploaded document"""
    from app.crud.document import document_crud
    from uuid import UUID
    
    document = document_crud.get(db, id=UUID(document_id))
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return {
        "document_id": str(document.id),
        "status": document.processing_status,
        "filename": document.filename,
        "text_extracted": bool(document.raw_text),
        "word_count": document.word_count,
        "error": document.processing_error
    }
```

---

## TASK 7: UPDATE MAIN APP TO INCLUDE UPLOAD ROUTER

```python
# app/main.py - ADD THIS

from app.api.v1 import upload

# Add to router includes
app.include_router(upload.router, prefix="/api/v1")
```

---

## TASK 8: CREATE FILE UTILITIES

```python
# app/utils/file_utils.py

"""
File utility functions
"""

from pathlib import Path
from typing import Optional
import hashlib


def get_file_extension(filename: str) -> str:
    """Get file extension without dot"""
    return Path(filename).suffix[1:].lower()


def get_safe_filename(filename: str) -> str:
    """
    Create safe filename by removing dangerous characters
    """
    # Remove path components
    filename = Path(filename).name
    
    # Replace spaces and special chars
    safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
    safe_name = "".join(c if c in safe_chars else "_" for c in filename)
    
    return safe_name


def calculate_file_hash(file_path: Path, algorithm: str = "md5") -> str:
    """Calculate file hash"""
    hash_obj = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def format_file_size(bytes: int) -> str:
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"
```

---

## TASK 9: CREATE TESTS

```python
# tests/test_services/test_text_extractor.py

"""
Test text extraction from various file types
"""

import pytest
from pathlib import Path
from app.services.text_extractor import text_extractor


class TestTextExtractor:
    """Test text extraction service"""
    
    def test_extract_pdf(self, sample_pdf):
        """Test PDF text extraction"""
        result = text_extractor.extract(sample_pdf)
        
        assert result['text']
        assert result['page_count'] > 0
        assert result['word_count'] > 0
        assert 'metadata' in result
    
    def test_extract_docx(self, sample_docx):
        """Test Word document extraction"""
        result = text_extractor.extract(sample_docx)
        
        assert result['text']
        assert result['word_count'] > 0
    
    def test_extract_image_ocr(self, sample_image):
        """Test OCR on image"""
        result = text_extractor.extract(sample_image)
        
        # OCR might not extract much from a blank image
        assert 'text' in result
        assert 'metadata' in result
    
    def test_unsupported_type(self):
        """Test error on unsupported file type"""
        with pytest.raises(ValueError, match="Unsupported file type"):
            text_extractor.extract(Path("/fake/file.xyz"))


# Fixtures for sample files
@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF for testing"""
    # You'll need to create actual sample files
    # or use existing test files
    pass

@pytest.fixture
def sample_docx(tmp_path):
    """Create a sample DOCX for testing"""
    pass

@pytest.fixture
def sample_image(tmp_path):
    """Create a sample image for testing"""
    pass
```

---

## EXECUTION INSTRUCTIONS

### Step 1: Install Dependencies
```bash
# Install Python packages
pip install -r requirements.txt

# Install system dependencies
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr poppler-utils libmagic1

# macOS:
brew install tesseract poppler libmagic
```

### Step 2: Create Directory Structure
```bash
mkdir -p data/{uploads,processed/{text,thumbnails},temp}
```

### Step 3: Implement Services
1. Create `app/services/storage.py` - File storage management
2. Create `app/services/text_extractor.py` - Text extraction
3. Create `app/services/thumbnail_generator.py` - Thumbnail generation
4. Create `app/services/document_processor.py` - Main orchestrator

### Step 4: Create Upload Endpoint
1. Create `app/api/v1/upload.py` - Upload API
2. Update `app/main.py` to include upload router

### Step 5: Create Utilities
1. Create `app/utils/file_utils.py` - Helper functions

### Step 6: Test Everything
```bash
# Start server
uvicorn app.main:app --reload

# Test upload via Swagger UI
open http://localhost:8000/docs

# Or use curl
curl -X POST "http://localhost:8000/api/v1/upload/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/test.pdf"
```

---

## TESTING CHECKLIST

Test via Swagger UI at `http://localhost:8000/docs`:

1. **Upload PDF**
   - [ ] File uploads successfully
   - [ ] Text is extracted
   - [ ] Word count is calculated
   - [ ] Thumbnail is generated
   - [ ] Status becomes "completed"

2. **Upload Word Document**
   - [ ] DOCX uploads and processes
   - [ ] Text extracted correctly
   - [ ] Metadata captured

3. **Upload Image**
   - [ ] Image uploads
   - [ ] OCR extracts text
   - [ ] Thumbnail generated

4. **Upload Excel/PowerPoint**
   - [ ] Files process correctly
   - [ ] Text from cells/slides extracted

5. **Error Handling**
   - [ ] File too large rejected
   - [ ] Invalid file type rejected
   - [ ] Corrupted file handled gracefully

6. **File Storage**
   - [ ] Files organized by date in uploads/
   - [ ] Thumbnails in processed/thumbnails/
   - [ ] Text in processed/text/

---

## COMMON ISSUES & SOLUTIONS

**Issue**: Tesseract not found
**Solution**: `sudo apt-get install tesseract-ocr` or `brew install tesseract`

**Issue**: PDF to image conversion fails
**Solution**: `sudo apt-get install poppler-utils` or `brew install poppler`

**Issue**: MIME type detection fails
**Solution**: `sudo apt-get install libmagic1` or `brew install libmagic`

**Issue**: Out of memory on large PDFs
**Solution**: Implement chunked processing or reduce OCR DPI

**Issue**: Permission denied on data/ directory
**Solution**: `chmod -R 755 data/` or check Docker volume permissions

---

## SUCCESS CRITERIA

✅ Can upload files via API  
✅ Text extracted from PDFs, DOCX, XLSX, PPTX  
✅ OCR works on images and scanned PDFs  
✅ Thumbnails generated for visual files  
✅ Files organized in date-based folders  
✅ Document status updates correctly  
✅ Error handling for invalid/corrupted files  
✅ All tests pass  

**When all criteria met, Sprint 2 is COMPLETE!** 🎉

---

## NEXT SPRINT PREVIEW

**Sprint 3: AI Analysis Integration** will add:
- Anthropic Claude API integration
- Document summarization
- Key points extraction
- Entity recognition
- Action item detection
- Auto-categorization

The upload pipeline you built will automatically queue documents for AI processing!
