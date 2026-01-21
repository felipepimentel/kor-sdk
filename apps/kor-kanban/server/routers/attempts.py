from fastapi import APIRouter
from typing import List, Optional
from datetime import datetime
import json
import os
from pathlib import Path

router = APIRouter(prefix="/api/task-attempts", tags=["attempts"])

DATA_DIR = Path("data")
ATTEMPTS_FILE = DATA_DIR / "attempts.json"

def load_attempts():
    if not ATTEMPTS_FILE.exists():
        return []
    try:
        with open(ATTEMPTS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_attempts(attempts):
    DATA_DIR.mkdir(exist_ok=True)
    with open(ATTEMPTS_FILE, "w") as f:
        json.dump(attempts, f, indent=2)

@router.get("")
def list_attempts(task_id: Optional[str] = None):
    all_attempts = load_attempts()
    if task_id:
        return {"success": True, "data": [w for w in all_attempts if w.get("task_id") == task_id]}
    return {"success": True, "data": all_attempts}

@router.get("/count")
def get_count():
    attempts = load_attempts()
    return {"success": True, "data": len(attempts)}

@router.get("/{attempt_id}")
def get_attempt(attempt_id: str):
    attempts = load_attempts()
    for w in attempts:
        if w["id"] == attempt_id:
            return {"success": True, "data": w}
    return {"success": False, "message": "Not found"}

@router.post("")
def create_attempt(data: dict):
    attempts = load_attempts()
    new_attempt = {
        "id": f"ws-{int(datetime.now().timestamp())}",
        "task_id": data.get("task_id"),
        "container_ref": f"container-{int(datetime.now().timestamp())}", # Mock container ref
        "branch": "main", # Default
        "agent_working_dir": "/app",
        "setup_completed_at": datetime.now().isoformat(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "archived": False,
        "pinned": False,
        "name": data.get("name", "New Workspace"),
        "is_running": False,
        "is_errored": False
    }
    attempts.append(new_attempt)
    save_attempts(attempts)
    return {"success": True, "data": new_attempt}

@router.get("/{attempt_id}/children")
def get_children(attempt_id: str):
    # Mock relationship
    return {
        "success": True, 
        "data": {
            "parent_task": None,
            "current_workspace": get_attempt(attempt_id).get("data"),
            "children": []
        }
    }
