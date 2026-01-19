"""
FastAPI application for KOR OpenAI-Compatible API.
"""

import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from .routes.chat import router as chat_router
from .routes.models import router as models_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key from environment (optional)
API_KEY = os.getenv("KOR_API_KEY", None)


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key if KOR_API_KEY is set."""
    
    async def dispatch(self, request: Request, call_next):
        from starlette.responses import JSONResponse
        
        # Skip auth for health check
        if request.url.path == "/health":
            return await call_next(request)
        
        if API_KEY:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={"error": {"message": "Missing API key", "type": "auth_error"}}
                )
            
            provided_key = auth_header.replace("Bearer ", "")
            if provided_key != API_KEY:
                return JSONResponse(
                    status_code=401,
                    content={"error": {"message": "Invalid API key", "type": "auth_error"}}
                )
        
        return await call_next(request)


app = FastAPI(
    title="KOR OpenAI-Compatible API",
    description="Exposes KOR agents via REST API",
    version="0.1.0"
)

# Add auth middleware
app.add_middleware(APIKeyMiddleware)

# Enable CORS for generic access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes under /v1 for compatibility
app.include_router(chat_router, prefix="/v1", tags=["Chat"])
app.include_router(models_router, prefix="/v1", tags=["Models"])

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "plugin": "kor-plugin-openai-api"}

def run(host: str = "0.0.0.0", port: int = 8000):
    """Entry point to run the FastAPI server."""
    logger.info(f"Starting KOR OpenAI API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run()
