from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
import uuid
from pathlib import Path

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


DATA_DIR = Path.home() / ".kor" / "data" / "kanban"
TASKS_FILE = DATA_DIR / "tasks.json"

def load_tasks() -> List[Dict[str, Any]]:
    if not TASKS_FILE.exists():
        return []
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_tasks(tasks: List[Dict[str, Any]]):
    DATA_DIR.mkdir(exist_ok=True)
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def broadcast_update(request: Request, background_tasks: BackgroundTasks, event_type: str, data: Any):
    manager = getattr(request.app.state, "connection_manager", None)
    if manager:
        background_tasks.add_task(manager.broadcast, {
            "type": event_type,
            "data": data
        })

@router.get("")
def list_tasks(project_id: Optional[str] = None):
    all_tasks = load_tasks()
    if project_id:
        return {"success": True, "data": [t for t in all_tasks if t.get("project_id") == project_id]}
    return {"success": True, "data": all_tasks}

@router.post("")
def create_task(data: dict, request: Request, background_tasks: BackgroundTasks):
    tasks = load_tasks()
    
    # Generate a proper UUID
    task_id = str(uuid.uuid4())
    
    new_task = {
        "id": task_id,
        "project_id": data.get("project_id"),
        "title": data.get("title", "New Task"),
        "description": data.get("description", ""),
        "status": data.get("status", "todo"),
        "parent_workspace_id": data.get("parent_workspace_id"),
        "image_ids": data.get("image_ids", []),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    tasks.append(new_task)
    save_tasks(tasks)
    
    broadcast_update(request, background_tasks, "task_created", new_task)
    
    return {"success": True, "data": new_task}

@router.get("/{task_id}")
def get_task(task_id: str):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            return {"success": True, "data": task}
    return {"success": False, "message": "Task not found"}

@router.put("/{task_id}")
def update_task(task_id: str, data: dict, request: Request, background_tasks: BackgroundTasks):
    tasks = load_tasks()
    found_idx = -1
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            found_idx = i
            break
    
    if found_idx == -1:
         return {"success": False, "message": "Task not found"}

    task = tasks[found_idx]
    
    # Update allowed fields
    for field in ["title", "description", "status", "parent_workspace_id", "image_ids"]:
        if field in data:
            task[field] = data[field]
            
    task["updated_at"] = datetime.now().isoformat()
    tasks[found_idx] = task
    
    save_tasks(tasks)
    
    broadcast_update(request, background_tasks, "task_updated", task)
    
    return {"success": True, "data": task}

@router.delete("/{task_id}")
def delete_task(task_id: str, request: Request, background_tasks: BackgroundTasks):
    tasks = load_tasks()
    original_len = len(tasks)
    
    # Find task to delete to broadcast it (or just ID)
    task_to_delete = next((t for t in tasks if t["id"] == task_id), None)
    
    tasks = [t for t in tasks if t["id"] != task_id]
    if len(tasks) < original_len:
        save_tasks(tasks)
        if task_to_delete:
            broadcast_update(request, background_tasks, "task_deleted", {"id": task_id, "project_id": task_to_delete.get("project_id")})
        return {"success": True}
    return {"success": False, "message": "Task not found"}

@router.get("/count")
def get_task_count():
    tasks = load_tasks()
    return {"success": True, "data": len(tasks)}
