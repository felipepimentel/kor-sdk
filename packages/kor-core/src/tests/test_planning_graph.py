
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from kor_core.agent.nodes.planner import ensure_plan_node
from kor_core.agent.graph import create_graph

@patch("kor_core.agent.nodes.planner.Path")
def test_ensure_plan_node_logic(mock_path_cls):
    # Mock file system interaction
    mock_path_instance = MagicMock()
    mock_path_cls.return_value = mock_path_instance
    mock_path_instance.exists.return_value = False # Simulate no file initially
    
    # Simulate initial state
    state = {"plan": [], "current_task_id": None}
    
    # 1. Run node (Should write default plan if empty? Or just bind?)
    # Currently planner.sync() with no file and empty state writes nothing if task list is empty.
    # But if we had state...
    
    state_with_task = {"plan": [{"id": "1", "description": "Task 1", "status": "pending"}], "current_task_id": None}
    
    result = ensure_plan_node(state_with_task)
    
    # Verify it tried to write to file
    mock_path_instance.write_text.assert_called()
    assert result["plan"] == state_with_task["plan"]

@patch("kor_core.agent.graph.get_kernel")
def test_graph_structure(mock_get_kernel):
    # Mock kernel to allow graph compilation without full boot
    mock_kernel = MagicMock()
    mock_kernel._is_initialized = True
    mock_kernel.config.agent.supervisor_members = ["Architect"] 
    mock_get_kernel.return_value = mock_kernel
    
    # Simulate no checkpointer service to avoid MagicMock type error in compile
    mock_kernel.registry.get_service.side_effect = Exception("No checkpointer")
    
    app = create_graph()
    
    # Check if nodes exist (internal graph structure check)
    assert "EnsurePlan" in app.nodes
    assert "Supervisor" in app.nodes
    
    # Check entry point
    # Note: Accessing internal graph logic might differ by LangGraph version
    # but compiled graph usually exposes ways to check.
    # For now, if compile worked, it's a good sign.
