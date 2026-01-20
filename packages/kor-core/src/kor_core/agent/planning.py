"""
Core Planning Logic for KOR Agents.

This module provides the "Brain" for Native Planning, allowing agents to:
1. Manage a structured list of tasks (The Plan).
2. Sync this plan with a physical markdown file (PLAN.md).
3. Track progress and self-correct.
"""
import re
from typing import List, Optional, Dict, Literal, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from .state import PlanTask

# Lazy import to avoid circular dependency
def _emit_event(event, **kwargs):
    """Helper to emit events via kernel hooks (safe import)."""
    try:
        from ..kernel import get_kernel
        from ..events import HookEvent
        kernel = get_kernel()
        if kernel and kernel._is_initialized:
            kernel.hooks.emit_sync(event, **kwargs)
    except Exception:
        pass  # Silent fail if hooks not available

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
        """Parses a markdown checklist into PlanTasks with hierarchy support."""
        if not self.file_path:
            return
            
        content = self.file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        
        new_tasks: List[PlanTask] = []
        id_counter = 0
        parent_stack: List[tuple] = []  # Stack of (depth, task_id)
        
        for line in lines:
            # Calculate indentation depth (each 2 spaces or 1 tab = 1 level)
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            depth = indent // 2  # Assuming 2-space indentation
            
            match = TASK_REGEX.match(line)
            if match:
                status_char = match.group(1)
                description = match.group(2).strip()
                
                status = "pending"
                if status_char == "x":
                    status = "completed"
                elif status_char == "/":
                    status = "active"
                
                id_counter += 1
                task_id = str(id_counter)
                
                # Determine parent based on depth
                parent_id = None
                
                # Pop from stack until we find a parent at lower depth
                while parent_stack and parent_stack[-1][0] >= depth:
                    parent_stack.pop()
                
                if parent_stack:
                    parent_id = parent_stack[-1][1]
                
                # Push current task to stack as potential parent
                parent_stack.append((depth, task_id))
                
                new_tasks.append({
                    "id": task_id,
                    "description": description,
                    "status": status,
                    "result": None,
                    "parent_id": parent_id,
                    "depth": depth
                })
        
        self.tasks = new_tasks
        
        # Auto-detect active task
        active_tasks = [t for t in self.tasks if t["status"] == "active"]
        if active_tasks:
            self.current_task_id = active_tasks[0]["id"]
        # If no active task and some pending, maybe next pending? 
        # For now, let's stick to explicit active status.

    def _write_to_file(self) -> None:
        """Writes PlanTasks to a markdown checklist with hierarchy support."""
        if not self.file_path or not self.tasks:
            return

        lines = ["# Agent Plan\n"]
        
        for task in self.tasks:
            symbol = " "
            if task["status"] == "completed":
                symbol = "x"
            elif task["status"] == "active":
                symbol = "/"
            
            # Add indentation based on depth
            depth = task.get("depth", 0)
            indent = "  " * depth
            lines.append(f"{indent}- [{symbol}] {task['description']}")
            
        self.file_path.write_text("\n".join(lines), encoding="utf-8")

    def add_task(self, description: str, parent_id: Optional[str] = None) -> None:
        """Adds a new pending task to the end of the plan."""
        from ..events import HookEvent
        
        new_id = str(len(self.tasks) + 1)
        
        # Calculate depth from parent
        depth = 0
        if parent_id:
            parent = next((t for t in self.tasks if t["id"] == parent_id), None)
            if parent:
                depth = parent.get("depth", 0) + 1
        
        self.tasks.append({
            "id": new_id,
            "description": description,
            "status": "pending",
            "result": None,
            "parent_id": parent_id,
            "depth": depth
        })
        if self.file_path:
            self._write_to_file()
        
        # Emit event
        _emit_event(HookEvent.PLAN_UPDATED, task_id=new_id, action="added", description=description)

    def update_task_status(self, task_id: str, status: str, result: Optional[str] = None) -> None:
        """Updates a task's status and persists."""
        from ..events import HookEvent
        
        target = next((t for t in self.tasks if t["id"] == task_id), None)
        if target:
            old_status = target["status"]
            target["status"] = status
            if result:
                target["result"] = result
            
            # Handle exclusivity of 'active' status if needed
            if status == "active":
                self.current_task_id = task_id
                
            if self.file_path:
                self._write_to_file()
            
            # Emit appropriate event
            if status == "active" and old_status != "active":
                _emit_event(HookEvent.TASK_STARTED, task_id=task_id, description=target["description"])
            elif status == "completed":
                _emit_event(HookEvent.TASK_COMPLETED, task_id=task_id, description=target["description"], result=result)
                
                # Check if entire plan is now complete
                if self.is_complete():
                    _emit_event(HookEvent.PLAN_FINISHED, tasks=self.tasks)
            else:
                _emit_event(HookEvent.PLAN_UPDATED, task_id=task_id, action="status_changed", new_status=status)

    def get_progress(self) -> Tuple[int, int]:
        """Returns (completed_count, total_count) for progress tracking."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t["status"] == "completed")
        return (completed, total)

    def is_complete(self) -> bool:
        """Returns True if all tasks are completed."""
        if not self.tasks:
            return False
        return all(t["status"] == "completed" for t in self.tasks)

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

