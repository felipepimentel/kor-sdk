"""
FastAPI application for KOR OpenAI-Compatible API.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .routes.chat import router as chat_router
from .routes.models import router as models_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="KOR OpenAI-Compatible API",
    description="Exposes KOR agents via REST API",
    version="0.1.0"
)

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
