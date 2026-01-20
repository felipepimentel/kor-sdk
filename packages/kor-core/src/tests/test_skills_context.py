import pytest
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

from kor_core.context.models import ContextQuery
from kor_core.context.skills import SkillResolver
from kor_core.context.exceptions import ContextError

@pytest.fixture
def temp_skills_dir(tmp_path):
    """Create a temporary skills directory structure."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    return skills_dir

@pytest.mark.asyncio
async def test_resolve_standard_skill(temp_skills_dir):
    """Test resolving a skill in standard format (folder/SKILL.md)."""
    skill_name = "test-skill"
    skill_dir = temp_skills_dir / skill_name
    skill_dir.mkdir()
    
    content = "---\nname: Test Skill\n---\n# Content"
    (skill_dir / "SKILL.md").write_text(content)
    
    resolver = SkillResolver()
    # Override search paths specifically for this test
    resolver.search_paths = [temp_skills_dir]
    
    result = await resolver.resolve(f"skill://{skill_name}", ContextQuery("uri"))
    
    assert len(result.items) == 1
    item = result.items[0]
    assert item.id == skill_name
    assert item.content == content
    assert item.metadata["format"] == "standard"

@pytest.mark.asyncio
async def test_resolve_legacy_skill(temp_skills_dir):
    """Test resolving a skill in legacy format (file.md)."""
    skill_name = "legacy-skill"
    content = "# Legacy Content"
    (temp_skills_dir / f"{skill_name}.md").write_text(content)
    
    resolver = SkillResolver()
    resolver.search_paths = [temp_skills_dir]
    
    result = await resolver.resolve(f"skill://{skill_name}", ContextQuery("uri"))
    
    assert len(result.items) == 1
    item = result.items[0]
    assert item.content == content
    assert item.metadata["format"] == "legacy"

@pytest.mark.asyncio
async def test_resolve_not_found(temp_skills_dir):
    """Test resolving a non-existent skill."""
    resolver = SkillResolver()
    resolver.search_paths = [temp_skills_dir]
    
    with pytest.raises(ContextError) as exc:
        await resolver.resolve("skill://missing", ContextQuery("uri"))
    
    assert "Skill not found" in str(exc.value)

@pytest.mark.asyncio
async def test_resolve_priority(temp_skills_dir):
    """Test that standard format takes priority over legacy if both exist."""
    skill_name = "mixed-skill"
    
    # Create Legacy
    (temp_skills_dir / f"{skill_name}.md").write_text("Legacy")
    
    # Create Standard
    skill_dir = temp_skills_dir / skill_name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("Standard")
    
    resolver = SkillResolver()
    resolver.search_paths = [temp_skills_dir]
    
    result = await resolver.resolve(f"skill://{skill_name}", ContextQuery("uri"))
    
    assert result.items[0].content == "Standard"
