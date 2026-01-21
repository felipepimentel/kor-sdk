from fastapi import APIRouter
from typing import List, Optional
from datetime import datetime
import json
import os
from pathlib import Path

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

DATA_DIR = Path("data")
TASKS_FILE = DATA_DIR / "tasks.json"

def load_tasks():
    if not TASKS_FILE.exists():
        return []
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_tasks(tasks):
    DATA_DIR.mkdir(exist_ok=True)
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

@router.get("")
def list_tasks(project_id: Optional[str] = None):
    all_tasks = load_tasks()
    if project_id:
        return {"success": True, "data": [t for t in all_tasks if t.get("project_id") == project_id]}
    return {"success": True, "data": all_tasks}

@router.post("")
def create_task(data: dict):
    tasks = load_tasks()
    new_task = {
        "id": f"task-{int(datetime.now().timestamp())}", # Simple unique ID
        "project_id": data.get("project_id"),
        "title": data.get("title", "New Task"),
        "description": data.get("description"),
        "status": data.get("status", "todo"),
        "parent_workspace_id": data.get("parent_workspace_id"),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    tasks.append(new_task)
    save_tasks(tasks)
    return {"success": True, "data": new_task}

@router.put("/{task_id}")
def update_task(task_id: str, data: dict):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            # Update fields
            if "title" in data: task["title"] = data["title"]
            if "description" in data: task["description"] = data["description"]
            if "status" in data: task["status"] = data["status"]
            task["updated_at"] = datetime.now().isoformat()
            save_tasks(tasks)
            return {"success": True, "data": task}
    return {"success": False, "message": "Task not found"}

@router.delete("/{task_id}")
def delete_task(task_id: str):
    tasks = load_tasks()
    original_len = len(tasks)
    tasks = [t for t in tasks if t["id"] != task_id]
    if len(tasks) < original_len:
        save_tasks(tasks)
        return {"success": True}
    return {"success": False, "message": "Task not found"}

@router.get("/count")
def get_task_count():
    tasks = load_tasks()
    return {"success": True, "data": len(tasks)}
