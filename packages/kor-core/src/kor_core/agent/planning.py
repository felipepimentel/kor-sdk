"""
Core Planning Logic for KOR Agents.

This module provides the "Brain" for Native Planning, allowing agents to:
1. Manage a structured list of tasks (The Plan).
2. Sync this plan with a physical markdown file (PLAN.md).
3. Track progress and self-correct.
"""
import re
from typing import List, Optional, Dict, Literal
from pathlib import Path
from dataclasses import dataclass, field
from .state import PlanTask

# Regular expressions for parsing markdown checklists
TASK_REGEX = re.compile(r'^\s*-\s*\[([ x/])\]\s*(.*)$')

@dataclass
class Planner:
    """
    Manages the agent's plan, serving as the bridge between 
    internal state (RAM) and external persistence (Markdown).
    """
    tasks: List[PlanTask] = field(default_factory=list)
    current_task_id: Optional[str] = None
    file_path: Optional[Path] = None

    @classmethod
    def from_state(cls, state_plan: List[PlanTask], current_task_id: Optional[str] = None) -> "Planner":
        """Reconstructs a Planner from the AgentState."""
        return cls(tasks=state_plan or [], current_task_id=current_task_id)

    def bind_to_file(self, path: Path) -> None:
        """Binds this planner to a physical file."""
        self.file_path = path

    def sync(self) -> None:
        """
        Synchronizes the plan with the file system.
        - If file exists: Read and update internal state.
        - If file missing: Write internal state to file.
        """
        if not self.file_path:
            return

        if self.file_path.exists():
            self._read_from_file()
        else:
            self._write_to_file()

    def _read_from_file(self) -> None:
        """Parses a markdown checklist into PlanTasks."""
        if not self.file_path:
            return
            
        content = self.file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        new_tasks: List[PlanTask] = []
        
        # Simple parser for now - assumes flat list or simple indentation
        # Structure: "- [Status] Description"
        for i, line in enumerate(lines):
            match = TASK_REGEX.match(line)
            if match:
                status_char = match.group(1)
                description = match.group(2).strip()
                
                status = "pending"
                if status_char == "x":
                    status = "completed"
                elif status_char == "/":
                    status = "active"
                
                # Generate a simple ID based on index if one isn't explicit
                # Future: Support parsing "ID. Description"
                task_id = str(len(new_tasks) + 1)
                
                new_tasks.append({
                    "id": task_id,
                    "description": description,
                    "status": status,
                    "result": None 
                })
        
        self.tasks = new_tasks
        
        # Auto-detect active task
        active_tasks = [t for t in self.tasks if t["status"] == "active"]
        if active_tasks:
            self.current_task_id = active_tasks[0]["id"]
        # If no active task and some pending, maybe next pending? 
        # For now, let's stick to explicit active status.

    def _write_to_file(self) -> None:
        """Writes PlanTasks to a markdown checklist."""
        if not self.file_path or not self.tasks:
            return

        lines = ["# Agent Plan\n"]
        
        for task in self.tasks:
            symbol = " "
            if task["status"] == "completed":
                symbol = "x"
            elif task["status"] == "active":
                symbol = "/"
                
            lines.append(f"- [{symbol}] {task['description']}")
            
        self.file_path.write_text("\n".join(lines), encoding="utf-8")

    def add_task(self, description: str) -> None:
        """Adds a new pending task to the end of the plan."""
        new_id = str(len(self.tasks) + 1)
        self.tasks.append({
            "id": new_id,
            "description": description,
            "status": "pending",
            "result": None
        })
        if self.file_path:
            self._write_to_file()

    def update_task_status(self, task_id: str, status: str, result: Optional[str] = None) -> None:
        """Updates a task's status and persists."""
        target = next((t for t in self.tasks if t["id"] == task_id), None)
        if target:
            target["status"] = status
            if result:
                target["result"] = result
            
            # Handle exclusivity of 'active' status if needed
            if status == "active":
                self.current_task_id = task_id
                # Optionally demote other active tasks?
                # For now let's allow multiple active but usually there is one focus.
                
            if self.file_path:
                self._write_to_file()

    def get_next_step(self) -> Optional[PlanTask]:
        """Determines the next thing to work on."""
        # 1. Return currently active task
        if self.current_task_id:
             t = next((t for t in self.tasks if t["id"] == self.current_task_id), None)
             if t and t["status"] == "active":
                 return t
        
        # 2. Or the first pending task
        for task in self.tasks:
             if task["status"] == "pending":
                 return task
                 
        return None
