# SPRINT 4: BACKGROUND PROCESSING & QUEUE - CURSOR/WINDSURF PROMPT

## SPRINT OVERVIEW

**Sprint 4 Goal**: Implement asynchronous background processing with Celery/Redis so uploads return immediately, processing happens in background workers, and users get real-time status updates via WebSocket.

**Duration**: 2 weeks  
**Prerequisites**: Sprint 1, 2, 3 completed (database, document processing, AI analysis all working)

---

## WHAT YOU'RE BUILDING

A production-ready background processing system that:
1. Returns upload responses immediately (no waiting for processing)
2. Processes documents asynchronously in background workers
3. Provides real-time status updates via WebSocket
4. Implements retry logic for failed tasks
5. Handles concurrent processing efficiently
6. Monitors queue health and processing status
7. Supports task prioritization
8. Enables batch processing

---

## ARCHITECTURE OVERVIEW

```
┌─────────────┐
│   Upload    │
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   FastAPI           │
│   - Save file       │
│   - Create record   │
│   - Queue task      │
│   - Return 201      │ ◄── IMMEDIATE RESPONSE
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Redis Queue       │
│   - Task queue      │
│   - Results cache   │
│   - WebSocket pub   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   Celery Workers    │
│   - Text extract    │
│   - AI analysis     │
│   - Thumbnails      │
│   - Retry on fail   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   WebSocket         │
│   - Status updates  │
│   - Progress %      │
│   - Completion      │
└─────────────────────┘
```

---

## FILES TO CREATE

```
backend/
├── app/
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── celery_app.py           [MAIN - Celery configuration]
│   │   ├── tasks.py                [Background tasks]
│   │   ├── scheduler.py            [Periodic tasks]
│   │   └── monitoring.py           [Queue monitoring]
│   │
│   ├── api/v1/
│   │   ├── websocket.py            [WebSocket endpoint - NEW]
│   │   └── queue.py                [Queue management - NEW]
│   │
│   ├── services/
│   │   └── notification.py         [WebSocket notifications - NEW]
│   │
│   └── config.py                    [UPDATE - add Celery/Redis config]
│
├── docker-compose.yml               [UPDATE - add Redis service]
├── requirements.txt                 [UPDATE - add Celery/Redis]
└── README.md                        [UPDATE - worker instructions]
```

---

## TASK 1: UPDATE REQUIREMENTS & DOCKER

### Update requirements.txt

```txt
# Existing dependencies from Sprint 1-3...

# Background Processing
celery==5.3.6                  # Task queue
redis==5.0.1                   # Message broker & cache
flower==2.0.1                  # Celery monitoring UI

# WebSocket
python-socketio==5.11.1        # WebSocket support
python-engineio==4.9.0         # Engine.IO server
```

**Install command**:
```bash
pip install celery==5.3.6 redis==5.0.1 flower==2.0.1 python-socketio==5.11.1 python-engineio==4.9.0
```

### Update docker-compose.yml

```yaml
# Add these services to your existing docker-compose.yml

services:
  # Existing app service...
  
  redis:
    image: redis:7-alpine
    container_name: doc-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: doc-celery-worker
    command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./data:/app/data
    depends_on:
      - redis
      - db
    restart: unless-stopped

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: doc-celery-beat
    command: celery -A app.workers.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - db
    restart: unless-stopped

  flower:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: doc-flower
    command: celery -A app.workers.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:  # Add this
```

### Update .env.example

```bash
# Existing environment variables...

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=true

# Worker Configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
CELERY_TASK_TIME_LIMIT=600
CELERY_TASK_SOFT_TIME_LIMIT=540

# Task Retry Configuration
CELERY_TASK_MAX_RETRIES=3
CELERY_TASK_DEFAULT_RETRY_DELAY=60
```

### Update app/config.py

```python
# app/config.py - ADD THESE SETTINGS

class Settings(BaseSettings):
    # Existing settings...
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    CELERY_TASK_SERIALIZER: str = os.getenv("CELERY_TASK_SERIALIZER", "json")
    CELERY_RESULT_SERIALIZER: str = os.getenv("CELERY_RESULT_SERIALIZER", "json")
    CELERY_ACCEPT_CONTENT: list = ["json"]
    CELERY_TIMEZONE: str = os.getenv("CELERY_TIMEZONE", "UTC")
    CELERY_ENABLE_UTC: bool = True
    
    # Worker settings
    CELERY_WORKER_CONCURRENCY: int = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = int(os.getenv("CELERY_WORKER_MAX_TASKS_PER_CHILD", "1000"))
    CELERY_TASK_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_TIME_LIMIT", "600"))
    CELERY_TASK_SOFT_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "540"))
    
    # Task retry
    CELERY_TASK_MAX_RETRIES: int = int(os.getenv("CELERY_TASK_MAX_RETRIES", "3"))
    CELERY_TASK_DEFAULT_RETRY_DELAY: int = int(os.getenv("CELERY_TASK_DEFAULT_RETRY_DELAY", "60"))
```

---

## TASK 2: CREATE CELERY APPLICATION

```python
# app/workers/celery_app.py

"""
Celery Application Configuration
Background task queue for document processing
"""

from celery import Celery
from celery.schedules import crontab
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "doc_intelligence",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.workers.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    accept_content=settings.CELERY_ACCEPT_CONTENT,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=settings.CELERY_ENABLE_UTC,
    
    # Task execution
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    
    # Task routing
    task_routes={
        'app.workers.tasks.process_document_task': {'queue': 'documents'},
        'app.workers.tasks.analyze_document_task': {'queue': 'ai_analysis'},
        'app.workers.tasks.generate_thumbnail_task': {'queue': 'thumbnails'},
    },
    
    # Task priority
    task_default_priority=5,
    
    # Result backend
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    
    # Beat schedule (periodic tasks)
    beat_schedule={
        'cleanup-old-results': {
            'task': 'app.workers.tasks.cleanup_old_results',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        'retry-failed-tasks': {
            'task': 'app.workers.tasks.retry_failed_tasks',
            'schedule': crontab(minute='*/30'),  # Every 30 minutes
        },
        'update-queue-stats': {
            'task': 'app.workers.tasks.update_queue_stats',
            'schedule': 60.0,  # Every minute
        },
    },
)


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery setup"""
    logger.info(f'Request: {self.request!r}')
    return 'Celery is working!'
```

---

## TASK 3: CREATE BACKGROUND TASKS

```python
# app/workers/tasks.py

"""
Background Tasks
Celery tasks for document processing
"""

from celery import Task
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Optional

from app.workers.celery_app import celery_app
from app.db.base import SessionLocal
from app.models.document import Document
from app.models.category import Category
from app.models.processing_queue import ProcessingQueue
from app.services.text_extractor import text_extractor
from app.services.thumbnail_generator import thumbnail_generator
from app.services.ai_analyzer import ai_analyzer
from app.services.categorizer import categorizer
from app.services.storage import storage
from app.services.notification import notification_service
from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management"""
    
    _db: Optional[Session] = None
    
    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    max_retries=settings.CELERY_TASK_MAX_RETRIES,
    default_retry_delay=settings.CELERY_TASK_DEFAULT_RETRY_DELAY
)
def process_document_task(self, document_id: str):
    """
    Main document processing task
    
    Steps:
    1. Extract text
    2. Generate thumbnail
    3. Update document record
    4. Queue for AI analysis
    """
    
    try:
        logger.info(f"Processing document {document_id}")
        
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return {"error": "Document not found"}
        
        # Update status
        document.processing_status = "processing"
        self.db.commit()
        
        # Send WebSocket update
        notification_service.send_status_update(
            document_id=document_id,
            status="processing",
            message="Extracting text from document..."
        )
        
        # Get file path
        file_path = Path(document.original_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Step 1: Extract text
        logger.info(f"Extracting text from {file_path}")
        extraction_result = text_extractor.extract(file_path)
        
        document.raw_text = extraction_result['text']
        document.page_count = extraction_result['page_count']
        document.word_count = extraction_result['word_count']
        document.extracted_metadata = extraction_result['metadata']
        
        # Save extracted text
        storage.save_text(str(document.id), extraction_result['text'])
        
        self.db.commit()
        
        # Update progress
        notification_service.send_status_update(
            document_id=document_id,
            status="processing",
            message="Generating thumbnail...",
            progress=40
        )
        
        # Step 2: Generate thumbnail
        logger.info("Generating thumbnail")
        thumbnail_bytes = thumbnail_generator.generate(file_path, document.mime_type)
        if thumbnail_bytes:
            storage.save_thumbnail(str(document.id), thumbnail_bytes)
        
        # Update progress
        notification_service.send_status_update(
            document_id=document_id,
            status="processing",
            message="Starting AI analysis...",
            progress=60
        )
        
        # Step 3: Queue for AI analysis
        analyze_document_task.apply_async(
            args=[document_id],
            priority=7  # Higher priority
        )
        
        document.processed_date = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Document {document_id} processed successfully")
        
        return {
            "document_id": document_id,
            "status": "success",
            "word_count": document.word_count
        }
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        
        # Update document status
        if document:
            document.processing_status = "failed"
            document.processing_error = str(e)
            self.db.commit()
        
        # Send error notification
        notification_service.send_status_update(
            document_id=document_id,
            status="failed",
            message=f"Processing failed: {str(e)}"
        )
        
        # Retry task
        raise self.retry(exc=e)


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    max_retries=settings.CELERY_TASK_MAX_RETRIES,
    default_retry_delay=settings.CELERY_TASK_DEFAULT_RETRY_DELAY
)
def analyze_document_task(self, document_id: str):
    """
    AI analysis task
    
    Steps:
    1. Get document text
    2. Analyze with Claude
    3. Apply categorization
    4. Update document record
    """
    
    try:
        logger.info(f"Analyzing document {document_id}")
        
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return {"error": "Document not found"}
        
        if not document.raw_text:
            logger.warning(f"Document {document_id} has no text to analyze")
            document.processing_status = "completed"
            self.db.commit()
            return {"error": "No text to analyze"}
        
        # Update progress
        notification_service.send_status_update(
            document_id=document_id,
            status="processing",
            message="Analyzing with AI...",
            progress=70
        )
        
        # Get existing categories
        categories = self.db.query(Category).all()
        category_names = [c.name for c in categories]
        
        # AI Analysis
        analysis = ai_analyzer.analyze_document(
            text=document.raw_text,
            filename=document.filename,
            existing_categories=category_names
        )
        
        if analysis:
            # Update document
            document.summary = analysis.get('summary')
            document.key_points = analysis.get('key_points', [])
            document.entities = analysis.get('entities', {})
            document.action_items = analysis.get('action_items', [])
            document.ai_tags = analysis.get('tags', [])
            
            # Apply category
            categorizer.apply_category(self.db, document, analysis)
            
            logger.info(f"AI analysis completed for {document_id}")
        
        # Update status
        document.processing_status = "completed"
        self.db.commit()
        
        # Send completion notification
        notification_service.send_status_update(
            document_id=document_id,
            status="completed",
            message="Document processed successfully!",
            progress=100,
            document=document.to_dict()
        )
        
        return {
            "document_id": document_id,
            "status": "completed",
            "summary": document.summary
        }
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        
        # Update status
        if document:
            document.processing_status = "completed"  # Mark as completed even if AI fails
            self.db.commit()
        
        # Send notification
        notification_service.send_status_update(
            document_id=document_id,
            status="completed",
            message="Processing completed (AI analysis failed)",
            progress=100
        )
        
        # Retry task
        raise self.retry(exc=e)


@celery_app.task(base=DatabaseTask, bind=True)
def generate_thumbnail_task(self, document_id: str):
    """
    Generate thumbnail for document
    Separated task for parallel processing
    """
    
    try:
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return {"error": "Document not found"}
        
        file_path = Path(document.original_path)
        if not file_path.exists():
            return {"error": "File not found"}
        
        thumbnail_bytes = thumbnail_generator.generate(file_path, document.mime_type)
        if thumbnail_bytes:
            storage.save_thumbnail(str(document.id), thumbnail_bytes)
            logger.info(f"Thumbnail generated for {document_id}")
        
        return {"document_id": document_id, "status": "success"}
        
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        raise self.retry(exc=e)


@celery_app.task(base=DatabaseTask)
def cleanup_old_results():
    """
    Periodic task to cleanup old task results
    Runs daily at 2 AM
    """
    
    logger.info("Cleaning up old task results")
    
    # Celery automatically cleans up results older than result_expires
    # This is just a placeholder for any additional cleanup
    
    # Could add:
    # - Delete old temp files
    # - Archive old processing logs
    # - Cleanup orphaned files
    
    return {"status": "success"}


@celery_app.task(base=DatabaseTask)
def retry_failed_tasks():
    """
    Periodic task to retry failed processing tasks
    Runs every 30 minutes
    """
    
    logger.info("Checking for failed tasks to retry")
    
    # Find documents stuck in processing
    stuck_documents = self.db.query(Document).filter(
        Document.processing_status == "processing",
        Document.upload_date < datetime.utcnow() - timedelta(hours=1)
    ).all()
    
    for doc in stuck_documents:
        logger.warning(f"Retrying stuck document {doc.id}")
        process_document_task.apply_async(args=[str(doc.id)])
    
    return {"retried": len(stuck_documents)}


@celery_app.task
def update_queue_stats():
    """
    Update queue statistics
    Runs every minute
    """
    
    # Get queue stats from Redis
    from redis import Redis
    redis_client = Redis.from_url(settings.REDIS_URL)
    
    stats = {
        'documents_queue': redis_client.llen('celery:documents'),
        'ai_analysis_queue': redis_client.llen('celery:ai_analysis'),
        'thumbnails_queue': redis_client.llen('celery:thumbnails'),
    }
    
    # Store in Redis for API access
    redis_client.setex('queue:stats', 300, str(stats))  # 5 min TTL
    
    return stats
```

---

## TASK 4: CREATE WEBSOCKET NOTIFICATION SERVICE

```python
# app/services/notification.py

"""
WebSocket Notification Service
Send real-time updates to connected clients
"""

from redis import Redis
from app.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Send real-time notifications via WebSocket
    Uses Redis pub/sub for message broadcasting
    """
    
    def __init__(self):
        self.redis = Redis.from_url(settings.REDIS_URL)
        self.channel_prefix = "document:"
    
    def send_status_update(
        self,
        document_id: str,
        status: str,
        message: str = "",
        progress: int = 0,
        document: dict = None
    ):
        """
        Send status update for a document
        
        Publishes to Redis channel: document:{document_id}
        """
        
        payload = {
            'type': 'status_update',
            'document_id': document_id,
            'status': status,
            'message': message,
            'progress': progress,
            'timestamp': str(datetime.utcnow())
        }
        
        if document:
            payload['document'] = document
        
        channel = f"{self.channel_prefix}{document_id}"
        
        try:
            self.redis.publish(channel, json.dumps(payload))
            logger.debug(f"Sent status update to {channel}: {status}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def send_batch_update(self, updates: list):
        """Send multiple updates at once"""
        
        for update in updates:
            self.send_status_update(**update)


# Singleton instance
notification_service = NotificationService()
```

---

## TASK 5: CREATE WEBSOCKET ENDPOINT

```python
# app/api/v1/websocket.py

"""
WebSocket Endpoint
Real-time status updates for document processing
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from redis import Redis
import asyncio
import json
import logging

from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: dict = {}
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    async def connect(self, websocket: WebSocket, document_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        if document_id not in self.active_connections:
            self.active_connections[document_id] = []
        
        self.active_connections[document_id].append(websocket)
        logger.info(f"Client connected for document {document_id}")
    
    def disconnect(self, websocket: WebSocket, document_id: str):
        """Remove WebSocket connection"""
        if document_id in self.active_connections:
            self.active_connections[document_id].remove(websocket)
            
            if not self.active_connections[document_id]:
                del self.active_connections[document_id]
        
        logger.info(f"Client disconnected from document {document_id}")
    
    async def send_message(self, message: str, websocket: WebSocket):
        """Send message to specific connection"""
        await websocket.send_text(message)
    
    async def broadcast(self, message: str, document_id: str):
        """Broadcast to all connections for a document"""
        if document_id in self.active_connections:
            for connection in self.active_connections[document_id]:
                await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/documents/{document_id}")
async def websocket_endpoint(websocket: WebSocket, document_id: str):
    """
    WebSocket endpoint for document processing updates
    
    Usage from frontend:
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/documents/{document_id}')
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log(data.status, data.progress, data.message)
    }
    """
    
    await manager.connect(websocket, document_id)
    
    # Subscribe to Redis channel
    pubsub = manager.redis.pubsub()
    channel = f"document:{document_id}"
    pubsub.subscribe(channel)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            'type': 'connected',
            'document_id': document_id,
            'message': 'WebSocket connected'
        })
        
        # Listen for Redis messages
        while True:
            # Check for Redis messages
            message = pubsub.get_message(ignore_subscribe_messages=True)
            
            if message and message['type'] == 'message':
                # Forward to WebSocket client
                await websocket.send_text(message['data'])
            
            # Also listen for client messages (if needed)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                # Handle client messages if needed
            except asyncio.TimeoutError:
                pass
            
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, document_id)
        pubsub.unsubscribe(channel)
        pubsub.close()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, document_id)
        pubsub.unsubscribe(channel)
        pubsub.close()
```

---

## TASK 6: CREATE QUEUE MANAGEMENT API

```python
# app/api/v1/queue.py

"""
Queue Management API
Monitor and manage background processing queues
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from redis import Redis
from celery import current_app
import logging

from app.api.deps import get_db
from app.config import settings
from app.models.document import Document
from app.workers.tasks import process_document_task

router = APIRouter(prefix="/queue", tags=["queue"])
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_queue_stats():
    """
    Get current queue statistics
    
    Returns:
    - Active workers
    - Queued tasks per queue
    - Processing status counts
    """
    
    redis_client = Redis.from_url(settings.REDIS_URL)
    
    # Get Celery stats
    stats = current_app.control.inspect().stats()
    active_tasks = current_app.control.inspect().active()
    
    # Get queue lengths
    queue_lengths = {
        'documents': redis_client.llen('celery:documents'),
        'ai_analysis': redis_client.llen('celery:ai_analysis'),
        'thumbnails': redis_client.llen('celery:thumbnails'),
    }
    
    return {
        'workers': len(stats) if stats else 0,
        'active_tasks': sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0,
        'queued_tasks': queue_lengths,
        'total_queued': sum(queue_lengths.values())
    }


@router.get("/workers")
async def get_worker_status():
    """Get status of all Celery workers"""
    
    stats = current_app.control.inspect().stats()
    active = current_app.control.inspect().active()
    
    if not stats:
        return {
            'workers': [],
            'message': 'No workers available'
        }
    
    workers = []
    for worker_name, worker_stats in stats.items():
        workers.append({
            'name': worker_name,
            'status': 'active',
            'pool': worker_stats.get('pool', {}).get('implementation', 'unknown'),
            'max_concurrency': worker_stats.get('pool', {}).get('max-concurrency', 0),
            'active_tasks': len(active.get(worker_name, [])) if active else 0
        })
    
    return {
        'workers': workers,
        'total': len(workers)
    }


@router.post("/documents/{document_id}/retry")
async def retry_document_processing(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Manually retry processing for a failed document
    """
    
    from uuid import UUID
    
    document = db.query(Document).filter(Document.id == UUID(document_id)).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Reset status
    document.processing_status = "pending"
    document.processing_error = None
    db.commit()
    
    # Queue task
    task = process_document_task.apply_async(args=[document_id], priority=9)
    
    return {
        'message': 'Processing queued',
        'document_id': document_id,
        'task_id': task.id
    }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific Celery task"""
    
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id, app=current_app)
    
    return {
        'task_id': task_id,
        'status': result.status,
        'result': result.result if result.ready() else None,
        'info': result.info
    }


@router.post("/purge")
async def purge_queue(queue_name: str = "documents"):
    """
    Purge all tasks from a specific queue
    USE WITH CAUTION - removes all pending tasks
    """
    
    if queue_name not in ['documents', 'ai_analysis', 'thumbnails']:
        raise HTTPException(status_code=400, detail="Invalid queue name")
    
    current_app.control.purge()
    
    return {
        'message': f'Queue {queue_name} purged',
        'queue': queue_name
    }
```

---

## TASK 7: UPDATE DOCUMENT PROCESSOR TO USE TASKS

```python
# app/services/document_processor.py - UPDATE process_upload

# Replace the synchronous processing with task queuing:

async def process_upload(
    self,
    db: Session,
    file: UploadFile,
    source: str = "upload"
) -> Document:
    """
    Process uploaded file - ASYNC VERSION
    
    Now just:
    1. Validate file
    2. Save to storage
    3. Create document record
    4. Queue background task
    5. Return immediately
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
        file_type=Path(file.filename).suffix[1:],
        file_size=file_size,
        mime_type=mime_type,
        source=source,
        processing_status="queued"  # Changed from "processing"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    logger.info(f"Created document record: {document.id}")
    
    # Step 4: Queue background task (NEW!)
    from app.workers.tasks import process_document_task
    
    task = process_document_task.apply_async(
        args=[str(document.id)],
        priority=5
    )
    
    logger.info(f"Queued processing task {task.id} for document {document.id}")
    
    # Step 5: Return immediately (NEW!)
    return document
```

---

## TASK 8: UPDATE MAIN APP

```python
# app/main.py - ADD THESE

from app.api.v1 import websocket, queue

# Add routers
app.include_router(websocket.router, prefix="/api/v1")
app.include_router(queue.router, prefix="/api/v1")

# Add startup event to check Redis connection
@app.on_event("startup")
async def startup_event():
    """Check Redis connection on startup"""
    from redis import Redis
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        redis.ping()
        logger.info("✓ Redis connection successful")
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
```

---

## TASK 9: CREATE STARTUP SCRIPTS

```bash
# scripts/start_worker.sh

#!/bin/bash

echo "Starting Celery worker..."

celery -A app.workers.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=documents,ai_analysis,thumbnails
```

```bash
# scripts/start_beat.sh

#!/bin/bash

echo "Starting Celery beat (periodic tasks)..."

celery -A app.workers.celery_app beat --loglevel=info
```

```bash
# scripts/start_flower.sh

#!/bin/bash

echo "Starting Flower (monitoring UI)..."

celery -A app.workers.celery_app flower --port=5555
```

Make them executable:
```bash
chmod +x scripts/start_worker.sh scripts/start_beat.sh scripts/start_flower.sh
```

---

## EXECUTION INSTRUCTIONS

### Step 1: Install Redis

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Step 2: Install Dependencies

```bash
pip install celery==5.3.6 redis==5.0.1 flower==2.0.1 python-socketio==5.11.1
```

### Step 3: Start Services

```bash
# Terminal 1: Start Redis (if not using Docker)
redis-server

# Terminal 2: Start FastAPI
uvicorn app.main:app --reload

# Terminal 3: Start Celery Worker
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 4: Start Celery Beat (periodic tasks)
celery -A app.workers.celery_app beat --loglevel=info

# Terminal 5: Start Flower (monitoring UI)
celery -A app.workers.celery_app flower
```

Or use Docker Compose:
```bash
docker-compose up
```

### Step 4: Verify Everything Works

```bash
# 1. Check Redis
redis-cli ping
# Should return: PONG

# 2. Check Celery worker
celery -A app.workers.celery_app inspect ping
# Should show active workers

# 3. Test upload
curl -X POST "http://localhost:8000/api/v1/upload/" \
  -F "file=@test.pdf"

# Response should be immediate with status="queued"

# 4. Check Flower dashboard
open http://localhost:5555
```

---

## TESTING CHECKLIST

### Background Processing
- [ ] Upload returns immediately (status="queued")
- [ ] Worker picks up task automatically
- [ ] Document status updates: queued → processing → completed
- [ ] Failed tasks retry automatically
- [ ] Multiple documents process concurrently

### WebSocket Updates
- [ ] WebSocket connects successfully
- [ ] Receives status updates in real-time
- [ ] Shows progress percentage
- [ ] Receives completion notification
- [ ] Handles connection drops gracefully

### Queue Management
- [ ] GET `/api/v1/queue/stats` shows queue status
- [ ] GET `/api/v1/queue/workers` lists active workers
- [ ] POST `/api/v1/queue/documents/{id}/retry` works
- [ ] Flower dashboard shows task history

### Error Handling
- [ ] Failed tasks retry up to max_retries
- [ ] Error messages sent via WebSocket
- [ ] Failed documents can be manually retried
- [ ] Worker crashes don't lose tasks

### Performance
- [ ] Can handle 10+ simultaneous uploads
- [ ] Workers process tasks in parallel
- [ ] No memory leaks over time
- [ ] Queue doesn't grow indefinitely

---

## TESTING WEBSOCKET FROM FRONTEND

```html
<!-- Test WebSocket connection -->
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Test</title>
</head>
<body>
    <h1>Document Processing Status</h1>
    <div id="status"></div>
    <div id="progress"></div>
    <div id="messages"></div>

    <script>
        const documentId = 'YOUR_DOCUMENT_ID_HERE';
        const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/documents/${documentId}`);
        
        ws.onopen = () => {
            console.log('WebSocket connected');
            document.getElementById('status').innerText = 'Connected';
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received:', data);
            
            document.getElementById('status').innerText = `Status: ${data.status}`;
            document.getElementById('progress').innerText = `Progress: ${data.progress}%`;
            
            const msgDiv = document.createElement('div');
            msgDiv.innerText = `${data.message} (${data.timestamp})`;
            document.getElementById('messages').appendChild(msgDiv);
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        ws.onclose = () => {
            console.log('WebSocket disconnected');
            document.getElementById('status').innerText = 'Disconnected';
        };
    </script>
</body>
</html>
```

---

## COMMON ISSUES & SOLUTIONS

**Issue**: "Cannot connect to Redis"
**Solution**: Start Redis: `redis-server` or `docker run -d -p 6379:6379 redis:7-alpine`

**Issue**: "No workers available"
**Solution**: Start worker: `celery -A app.workers.celery_app worker --loglevel=info`

**Issue**: Tasks not executing
**Solution**: Check worker logs for errors, verify task is registered

**Issue**: WebSocket not receiving updates
**Solution**: Check Redis pub/sub, verify notification_service is calling redis.publish

**Issue**: Tasks failing silently
**Solution**: Check Flower dashboard at http://localhost:5555 for error details

**Issue**: Worker memory usage growing
**Solution**: Lower `CELERY_WORKER_MAX_TASKS_PER_CHILD` or add more workers

---

## SUCCESS CRITERIA

✅ Upload returns immediately (< 100ms response time)  
✅ Background worker processes documents asynchronously  
✅ WebSocket sends real-time status updates  
✅ Failed tasks retry automatically  
✅ Multiple workers process concurrently  
✅ Flower dashboard shows all tasks  
✅ Queue stats API returns accurate data  
✅ Periodic cleanup tasks run  
✅ Can handle 100+ documents in queue  
✅ All tests pass  

**When all criteria met, Sprint 4 is COMPLETE!** 🎉

---

## MONITORING & DEBUGGING

### Flower Dashboard
Access at `http://localhost:5555`:
- View all tasks (active, succeeded, failed)
- Monitor worker health
- See task execution times
- Retry failed tasks manually

### Redis CLI
```bash
# Check queue lengths
redis-cli llen celery:documents

# Monitor pub/sub messages
redis-cli psubscribe "document:*"

# Check task results
redis-cli keys "celery-task-meta-*"
```

### Celery Inspect
```bash
# Check active tasks
celery -A app.workers.celery_app inspect active

# Check worker stats
celery -A app.workers.celery_app inspect stats

# Check registered tasks
celery -A app.workers.celery_app inspect registered
```

---

**Phase 1 is now COMPLETE!** 🚀

You have a fully functional backend with:
- Database & models ✅
- Document processing ✅
- AI analysis ✅
- Background queue ✅

Ready to move to **Phase 2: Cloud Integrations** (Gmail, Drive, Dropbox)?
