
import pytest
from pathlib import Path
from unittest.mock import patch
from kor_core.agent.planning import Planner
from kor_core.agent.archiver import PlanArchiver

def test_planner_is_complete():
    """Test is_complete method."""
    planner = Planner()
    
    # Empty plan is not complete
    assert not planner.is_complete()
    
    # Plan with pending tasks is not complete
    planner.tasks = [
        {"id": "1", "description": "Task 1", "status": "pending", "result": None, "parent_id": None, "depth": 0},
    ]
    assert not planner.is_complete()
    
    # Plan with all completed is complete
    planner.tasks = [
        {"id": "1", "description": "Task 1", "status": "completed", "result": None, "parent_id": None, "depth": 0},
        {"id": "2", "description": "Task 2", "status": "completed", "result": None, "parent_id": None, "depth": 0},
    ]
    assert planner.is_complete()

def test_archiver_archive_plan(tmp_path):
    """Test plan archiving."""
    memory_file = tmp_path / "plans.jsonl"
    archiver = PlanArchiver(memory_path=memory_file)
    
    tasks = [
        {"id": "1", "description": "Setup project", "status": "completed", "result": "Done"},
        {"id": "2", "description": "Write tests", "status": "completed", "result": "Done"},
        {"id": "3", "description": "Document code", "status": "pending", "result": None},
    ]
    
    archived = archiver.archive_plan(
        user_goal="Create a new API",
        plan_tasks=tasks
    )
    
    assert archived.tasks_completed == 2
    assert archived.tasks_total == 3
    assert memory_file.exists()
    
    # Verify file content
    content = memory_file.read_text()
    assert "Create a new API" in content

def test_archiver_get_success_rate(tmp_path):
    """Test success rate calculation."""
    memory_file = tmp_path / "plans.jsonl"
    archiver = PlanArchiver(memory_path=memory_file)
    
    # Archive two plans
    archiver.archive_plan("Goal 1", [
        {"id": "1", "description": "T1", "status": "completed", "result": None},
        {"id": "2", "description": "T2", "status": "completed", "result": None},
    ])
    archiver.archive_plan("Goal 2", [
        {"id": "1", "description": "T1", "status": "completed", "result": None},
        {"id": "2", "description": "T2", "status": "pending", "result": None},
    ])
    
    rate = archiver.get_success_rate()
    assert rate == 0.75  # 3 out of 4 tasks completed
