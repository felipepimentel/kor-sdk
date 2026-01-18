"""
Models routes.
"""

from fastapi import APIRouter
from ..schemas.models import ModelsResponse, KOR_MODELS

router = APIRouter()

from kor_core import Kernel
from ..schemas.models import ModelsResponse, Model
import time

@router.get("/v1/models", response_model=ModelsResponse)
@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """Lists the available KOR agents as models."""
    from kor_core.kernel import get_kernel
    kernel = get_kernel()
    try:
        kernel.boot()
    except Exception:
        pass
    
    registry = kernel.registry.get_service("agents")
    agents = registry.list_agents() if registry else {}
    
    data = []
    # Add dynamic agents
    for agent_id in agents.keys():
        data.append(Model(
            id=agent_id,
            created=1677610602,
            owned_by="kor"
        ))
    
    # Add static defaults
    from ..schemas.models import KOR_MODELS
    for m in KOR_MODELS:
        if m.id not in [d.id for d in data]:
            data.append(m)
        
    return ModelsResponse(data=data)
