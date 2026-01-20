
import pytest
from pathlib import Path
from kor_core.agent.planning import Planner

def test_planner_create_and_add_task():
    planner = Planner()
    planner.add_task("First Task")
    
    assert len(planner.tasks) == 1
    assert planner.tasks[0]["description"] == "First Task"
    assert planner.tasks[0]["status"] == "pending"

def test_planner_update_status():
    planner = Planner()
    planner.add_task("Task 1")
    task_id = planner.tasks[0]["id"]
    
    planner.update_task_status(task_id, "active")
    assert planner.tasks[0]["status"] == "active"
    assert planner.current_task_id == task_id

def test_planner_file_sync_write(tmp_path):
    plan_file = tmp_path / "PLAN.md"
    planner = Planner()
    planner.bind_to_file(plan_file)
    
    planner.add_task("Build API")
    planner.update_task_status(planner.tasks[0]["id"], "active")
    
    # Assert file was written
    content = plan_file.read_text()
    assert "# Agent Plan" in content
    assert "- [/] Build API" in content

def test_planner_file_sync_read(tmp_path):
    plan_file = tmp_path / "PLAN.md"
    plan_file.write_text("""# My Plan
- [ ] Task A
- [x] Task B
- [/] Task C
""")
    
    planner = Planner()
    planner.bind_to_file(plan_file)
    planner.sync()
    
    assert len(planner.tasks) == 3
    assert planner.tasks[0]["description"] == "Task A"
    assert planner.tasks[0]["status"] == "pending"
    
    assert planner.tasks[1]["description"] == "Task B"
    assert planner.tasks[1]["status"] == "completed"
    
    assert planner.tasks[2]["description"] == "Task C"
    assert planner.tasks[2]["status"] == "active"
    
    assert planner.current_task_id == planner.tasks[2]["id"]
