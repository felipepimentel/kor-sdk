from fastapi import APIRouter
from typing import List
from datetime import datetime
import os
from pathlib import Path

# Try to import KOR SDK components
try:
    from kor import Kernel
    from kor.context import ProjectContext
except ImportError:
    # Fallback/Mock if KOR SDK is not available in the env (shouldn't happen in prod)
    Kernel = None
    ProjectContext = None

router = APIRouter(prefix="/api/projects", tags=["projects"])

WORKSPACE_ROOT = Path(os.path.expanduser("~/Workspace/kor-sdk"))

@router.get("")
def list_projects():
    # Real implementation: List subdirectories in WORKSPACE_ROOT as "Projects"
    # This is a basic integration.
    projects = []
    
    if WORKSPACE_ROOT.exists():
        for item in WORKSPACE_ROOT.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                projects.append({
                    "id": item.name, # Use dirname as ID for now
                    "name": item.name,
                    "default_agent_working_dir": str(item),
                    "remote_project_id": None,
                    "created_at": datetime.fromtimestamp(item.stat().st_ctime).isoformat(),
                    "updated_at": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
    
    return {"success": True, "data": projects}

@router.post("")
def create_project(data: dict):
    # Basic creation: Make a directory
    name = data.get("name")
    if not name:
        return {"success": False, "message": "Name is required"}
        
    project_path = WORKSPACE_ROOT / name
    if project_path.exists():
        return {"success": False, "message": "Project already exists"}
        
    try:
        project_path.mkdir(parents=True, exist_ok=True)
        new_project = {
            "id": name,
            "name": name,
            "default_agent_working_dir": str(project_path),
            "remote_project_id": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        return {"success": True, "data": new_project}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/{project_id}/repositories")
def list_repos(project_id: str):
    # Return empty list for now, or check for .git
    return {"success": True, "data": []}
