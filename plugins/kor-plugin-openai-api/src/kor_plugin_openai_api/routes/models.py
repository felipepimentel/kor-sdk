"""
Models routes.
"""

from fastapi import APIRouter
from ..schemas.models import ModelsResponse, KOR_MODELS

router = APIRouter()

@router.get("/models")
async def list_models():
    """
    Lists available KOR models in OpenAI format.
    """
    return ModelsResponse(data=KOR_MODELS)
