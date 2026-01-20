
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from kor_core.agent.planning import Planner
from kor_core.events import HookEvent

def test_planner_get_progress():
    """Test progress tracking method."""
    planner = Planner()
    planner.tasks = [
        {"id": "1", "description": "Task 1", "status": "completed", "result": None},
        {"id": "2", "description": "Task 2", "status": "active", "result": None},
        {"id": "3", "description": "Task 3", "status": "pending", "result": None},
    ]
    
    completed, total = planner.get_progress()
    assert completed == 1
    assert total == 3

@patch("kor_core.agent.planning._emit_event")
def test_planner_emits_events_on_status_change(mock_emit):
    """Test that status changes emit appropriate events."""
    planner = Planner()
    planner.tasks = [
        {"id": "1", "description": "Test Task", "status": "pending", "result": None},
    ]
    
    # Change to active -> should emit TASK_STARTED
    planner.update_task_status("1", "active")
    mock_emit.assert_called_with(
        HookEvent.TASK_STARTED, 
        task_id="1", 
        description="Test Task"
    )
    
    mock_emit.reset_mock()
    
    # Change to completed -> should emit TASK_COMPLETED (and PLAN_FINISHED after)
    planner.update_task_status("1", "completed", result="Done!")
    # Use assert_any_call since PLAN_FINISHED is emitted after
    mock_emit.assert_any_call(
        HookEvent.TASK_COMPLETED, 
        task_id="1", 
        description="Test Task",
        result="Done!"
    )

@patch("kor_core.agent.planning._emit_event")
def test_planner_emits_event_on_add_task(mock_emit):
    """Test that adding a task emits PLAN_UPDATED."""
    planner = Planner()
    planner.add_task("New Task")
    
    mock_emit.assert_called_with(
        HookEvent.PLAN_UPDATED,
        task_id="1",
        action="added",
        description="New Task"
    )
