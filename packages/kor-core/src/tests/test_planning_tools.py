
import pytest
from pathlib import Path
from unittest.mock import patch
from kor_core.tools.planning import ManagePlanTool

def test_manage_plan_tool_add_task(tmp_path):
    tool = ManagePlanTool()
    
    # Run in tmp dir to avoid messing with real PLAN.md
    with patch("kor_core.tools.planning.Path") as mock_path:
        # Map "PLAN.md" to a temp file
        temp_plan = tmp_path / "PLAN.md"
        
        # When Path("PLAN.md") is called, return our temp path
        # Note: mocking Path constructor is tricky because it's allowed to be instantiated
        # We might need to mock cwd or change usage in tool to respect an env var or argument.
        # But for now, let's just chdir or rely on the tool using Path("PLAN.md")
        pass

    # Easier approach: Use os.chdir
    import os
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # 1. Add Task
        result = tool._run(action="add_task", description="New Task")
        assert "Task added" in result
        
        # Verify file
        content = (tmp_path / "PLAN.md").read_text()
        assert "- [ ] New Task" in content
        
        # 2. Update Task
        # We need the ID. The first task is ID '1'
        result = tool._run(action="update_status", task_id="1", status="active")
        assert "updated to active" in result
        
        content = (tmp_path / "PLAN.md").read_text()
        assert "- [/] New Task" in content
        
        # 3. Finish Task
        result = tool._run(action="finish_task", task_id="1")
        assert "marked as completed" in result
        
        content = (tmp_path / "PLAN.md").read_text()
        assert "- [x] New Task" in content
        
    finally:
        os.chdir(cwd)
