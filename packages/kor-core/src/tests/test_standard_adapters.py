import pytest
import tempfile
import shutil
from pathlib import Path
from kor_core.context import (
    LocalContextSource, LocalResolver,
    ScriptResolver, ContextQuery
)

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)

@pytest.mark.asyncio
async def test_local_source_read_file(temp_dir):
    # Setup
    test_file = temp_dir / "test.txt"
    test_file.write_text("hello world", encoding="utf-8")
    
    source = LocalContextSource(root_dir=temp_dir)
    items = await source.fetch("local://test.txt", ContextQuery(uri="local://test.txt"))
    
    assert len(items) == 1
    assert items[0].content == "hello world"
    assert items[0].id == "test.txt"

@pytest.mark.asyncio
async def test_local_resolver(temp_dir):
    test_file = temp_dir / "test.txt"
    test_file.write_text("resolved content", encoding="utf-8")
    
    # We patch the source inside the resolver or instantiate it with the dir?
    # LocalResolver uses default LocalContextSource(root_dir=cwd).
    # We should probably allow injecting source or root_dir.
    # For now, let's change cwd or patch. Changing cwd is risky.
    # Let's subclass or monkeypatch.
    
    resolver = LocalResolver()
    resolver.source = LocalContextSource(root_dir=temp_dir)
    
    result = await resolver.resolve("local://test.txt", ContextQuery(uri="local://test.txt"))
    assert result.items[0].content == "resolved content"

@pytest.mark.asyncio
async def test_script_resolver(temp_dir):
    resolver = ScriptResolver()
    
    # Create temp script
    script_path = temp_dir / "echo.py"
    script_path.write_text("print('hello script')")
    
    # Run script
    uri = f"run:{script_path}"
    
    result = await resolver.resolve(uri, ContextQuery(uri=uri))
    assert "hello script" in result.items[0].content.strip()
