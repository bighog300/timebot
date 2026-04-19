"""
AI-Powered Document Organization Tool
Main application entry point
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path
from anthropic import Anthropic

# Initialize FastAPI app
app = FastAPI(
    title="Document Organizer",
    description="AI-powered document management and organization",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Ensure data directories exist
UPLOAD_PATH = Path(os.getenv("UPLOAD_PATH", "/app/data/uploads"))
PROCESSED_PATH = Path(os.getenv("PROCESSED_PATH", "/app/data/processed"))
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
PROCESSED_PATH.mkdir(parents=True, exist_ok=True)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "doc-organizer",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to AI Document Organizer",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document for processing
    """
    try:
        # Save the uploaded file
        file_path = UPLOAD_PATH / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # TODO: Add document processing logic here
        # - Extract text
        # - Analyze with Claude
        # - Generate tags and categories
        # - Store in database
        
        return {
            "message": "Document uploaded successfully",
            "filename": file.filename,
            "size": len(content),
            "path": str(file_path)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/analyze")
async def analyze_document(document_id: str):
    """
    Analyze a document using AI
    """
    try:
        # TODO: Implement AI analysis
        # - Load document content
        # - Send to Claude for analysis
        # - Extract categories, tags, summary
        
        message = anthropic_client.messages.create(
            model=os.getenv("AI_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": "Analyze this document and provide categories and tags."
                }
            ]
        )
        
        return {
            "document_id": document_id,
            "analysis": message.content[0].text
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/search")
async def search_documents(query: str):
    """
    Search documents using semantic search
    """
    try:
        # TODO: Implement semantic search
        # - Embed the query
        # - Search vector database
        # - Return ranked results
        
        return {
            "query": query,
            "results": [],
            "message": "Search functionality coming soon"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )
