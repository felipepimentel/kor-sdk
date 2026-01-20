import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from kor_core.tools.context import GetContextTool
from kor_core.skills import SkillLoader
from kor_core.context.models import ContextResult, ContextItem

@pytest.mark.asyncio
async def test_get_context_tool():
    """Test the GetContextTool."""
    # Mock ContextManager
    with patch("kor_core.tools.context.get_context_manager") as mock_get:
        cm = AsyncMock()
        mock_get.return_value = cm
        
        cm.resolve.return_value = ContextResult(items=[
            ContextItem(id="test", content="Context Content")
        ])
        
        tool = GetContextTool()
        result = await tool.ainvoke({"uri": "local://test.md"})
        
        assert result == "Context Content"
        cm.resolve.assert_called_once()

def test_skill_loader_deprecation():
    """Test that SkillLoader emits deprecation warning."""
    with pytest.warns(DeprecationWarning, match="deprecated"):
        SkillLoader()

def test_skill_loader_discovery_std(tmp_path):
    """Test that SkillLoader discovers skills in .agent/skills."""
    agent_dir = tmp_path / ".agent"
    skills_dir = agent_dir / "skills"
    skills_dir.mkdir(parents=True)
    
    # Create standard skill
    (skills_dir / "git").mkdir()
    (skills_dir / "git" / "SKILL.md").write_text("---\nname: git\n---\n# Git Skill")
    
    # Mock CWD to temp path
    with patch("pathlib.Path.cwd", return_value=tmp_path):
        with pytest.warns(DeprecationWarning):
            loader = SkillLoader()
            skills = loader.load_from_config_dir()
            
            assert len(skills) >= 1
            names = [s.name for s in skills]
            assert "git" in names
