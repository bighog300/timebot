"""
Local development entry point.

Usage:
    python app.py

Equivalent to:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 [--reload]

The Dockerfile and docker-compose.yml invoke uvicorn directly and do not
use this file. It exists purely as a convenience for local dev.
"""
import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
