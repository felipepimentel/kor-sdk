"""
Pydantic schemas for OpenAI Models API.

These models match the official OpenAI /v1/models endpoint.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel
import time


class Model(BaseModel):
    """A model object as returned by the API."""
    id: str
    object: Literal["model"] = "model"
    created: int
    owned_by: str


class ModelsResponse(BaseModel):
    """Response body for /v1/models endpoint."""
    object: Literal["list"] = "list"
    data: List[Model]


# Available KOR models
KOR_MODELS = [
    Model(
        id="kor-agent-v1",
        created=int(time.time()),
        owned_by="kor"
    ),
    Model(
        id="kor-agent-fast",
        created=int(time.time()),
        owned_by="kor"
    ),
]
