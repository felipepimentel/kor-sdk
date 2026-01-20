from typing import Optional, Type, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from pathlib import Path
from ..agent.planning import Planner

class ManagePlanInput(BaseModel):
    action: str = Field(..., description="Action to perform: 'add_task', 'add_subtask', 'update_status', 'finish_task'")
    task_id: Optional[str] = Field(None, description="Task ID for update/finish actions")
    description: Optional[str] = Field(None, description="Description for new tasks")
    status: Optional[str] = Field(None, description="New status for update action (pending, active, completed)")
    parent_id: Optional[str] = Field(None, description="Parent task ID for subtasks")

class ManagePlanTool(BaseTool):
    name: str = "manage_plan"
    description: str = (
        "Use this tool to manage the plan. "
        "Actions: "
        "'add_task': Add a new root task (requires description). "
        "'add_subtask': Add a subtask under a parent (requires description and parent_id). "
        "'update_status': Update a task status (requires task_id and status). "
        "'finish_task': Mark a task as completed (requires task_id). "
        "The plan is stored in PLAN.md."
    )
    args_schema: Type[BaseModel] = ManagePlanInput

    def _run(self, action: str, task_id: Optional[str] = None, description: Optional[str] = None, status: Optional[str] = None, parent_id: Optional[str] = None) -> str:
        try:
            # Initialize Planner bound to PLAN.md
            # We assume the CWD is the workspace root
            plan_path = Path("PLAN.md")
            planner = Planner()
            planner.bind_to_file(plan_path)
            planner.sync()  # Load current plan

            if action == "add_task":
                if not description:
                    return "Error: 'description' is required for 'add_task'."
                planner.add_task(description)
                return f"Task added: {description}"

            elif action == "add_subtask":
                if not description or not parent_id:
                    return "Error: 'description' and 'parent_id' are required for 'add_subtask'."
                planner.add_task(description, parent_id=parent_id)
                return f"Subtask added under task {parent_id}: {description}"

            elif action == "update_status":
                if not task_id or not status:
                    return "Error: 'task_id' and 'status' are required for 'update_status'."
                planner.update_task_status(task_id, status)
                return f"Task {task_id} updated to {status}."

            elif action == "finish_task":
                if not task_id:
                    return "Error: 'task_id' is required for 'finish_task'."
                planner.update_task_status(task_id, "completed")
                return f"Task {task_id} marked as completed."

            else:
                return f"Error: Unknown action '{action}'."

        except Exception as e:
            return f"Error managing plan: {str(e)}"
