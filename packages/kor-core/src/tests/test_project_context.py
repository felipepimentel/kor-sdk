import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from kor_core.context.manager import ContextManager
from kor_core.context.project import ProjectContextDetector

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project with .agent structure."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()
    
    (agent_dir / "AGENTS.md").write_text("# Agents")
    (agent_dir / "rules.md").write_text("# Rules")
    (agent_dir / "memories").mkdir()
    
    return tmp_path

def test_detector_finds_standard_files(temp_project):
    """Test that detector finds standard files."""
    mappings = ProjectContextDetector.detect(temp_project)
    
    assert "project:root" in mappings
    assert mappings["project:root"] == "local://.agent/"
    
    assert "project:agent" in mappings
    assert mappings["project:agent"] == "local://.agent/AGENTS.md"
    
    assert "project:rules" in mappings
    assert mappings["project:rules"] == "local://.agent/rules.md"
    
    assert "project:memory" in mappings
    assert mappings["project:memory"] == "local://.agent/memories"

def test_detector_handles_missing_files(tmp_path):
    """Test that missing files are not mapped."""
    # Empty project
    mappings = ProjectContextDetector.detect(tmp_path)
    
    # Should be empty as .agent dir doesn't exist
    assert mappings == {}
    
    # Create .agent but empty
    (tmp_path / ".agent").mkdir()
    mappings = ProjectContextDetector.detect(tmp_path)
    
    assert "project:root" in mappings
    assert "project:agent" not in mappings

def test_detector_alternatives(tmp_path):
    """Test alternative filenames."""
    agent_dir = tmp_path / ".agent"
    agent_dir.mkdir()
    
    # Use AGENT.md instead of AGENTS.md
    (agent_dir / "AGENT.md").write_text("# Agents")
    
    mappings = ProjectContextDetector.detect(tmp_path)
    
    assert "project:agent" in mappings
    assert mappings["project:agent"] == "local://.agent/AGENT.md"

@pytest.mark.asyncio
async def test_manager_integration(temp_project):
    """Test ContextManager integration."""
    # Reset singleton
    ContextManager._instance = None
    
    # Mock Path.cwd to return temp_project
    with patch("pathlib.Path.cwd", return_value=temp_project):
        cm = ContextManager()
        
        # Verify mappings loaded
        assert "project:agent" in cm.project_mappings
        assert cm.project_mappings["project:agent"] == "local://.agent/AGENTS.md"
        
        # Test resolution logic (without actual resolver, just mapping check)
        mapped = cm._apply_mapping("project:agent")
        assert mapped == "local://.agent/AGENTS.md"
        
        # Test default config override
        cm.load_config({"project:agent": "git://custom"})
        mapped = cm._apply_mapping("project:agent")
        assert mapped == "git://custom"
