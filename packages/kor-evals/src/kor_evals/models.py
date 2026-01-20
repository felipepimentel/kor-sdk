from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class Assertion(BaseModel):
    """
    Evaluation assertion rule.
    """
    type: str = Field(..., description="Type of assertion: file_exists, file_content_match, command_output_match")
    target: str = Field(..., description="Target file or command check")
    value: Optional[str] = Field(None, description="Expected value (regex or exact)")

class EvalCase(BaseModel):
    """
    Defines a single evaluation scenario.
    """
    id: str
    description: str
    
    # Setup
    initial_files: Dict[str, str] = Field(default_factory=dict, description="Files to populate in sandbox before run")
    agent_prompt: str = Field(..., description="Instruction to send to the agent")
    
    # Verification
    assertions: List[Assertion] = Field(default_factory=list)
    
    # Metadata
    difficulty: int = 1
    tags: List[str] = Field(default_factory=list)

class EvalResult(BaseModel):
    """
    Result of an evaluation run.
    """
    case_id: str
    success: bool
    score: float
    duration_ms: float
    error: Optional[str] = None
    assertion_results: List[Dict[str, Any]] = Field(default_factory=list)
