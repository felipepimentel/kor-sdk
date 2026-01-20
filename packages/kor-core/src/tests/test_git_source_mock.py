import pytest
import asyncio
import shutil
import tempfile
from pathlib import Path
from kor_core.context import GitContextSource, ContextQuery

@pytest.fixture
def temp_dirs():
    """Returns (origin_dir, cache_dir)"""
    root = tempfile.mkdtemp()
    origin = Path(root) / "origin"
    origin.mkdir()
    cache = Path(root) / "cache"
    cache.mkdir()
    yield origin, cache
    shutil.rmtree(root)

async def run_git(args, cwd):
    proc = await asyncio.create_subprocess_exec(
        "git", *args, cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    if proc.returncode != 0:
        print(f"Git command failed: git {' '.join(args)}")
        print(f"Error: {err.decode()}")
        print(f"Output: {out.decode()}")
        raise Exception(f"Git failed: {err.decode()}")
    return out.decode()

async def init_git_repo(path: Path):
    """Initialize a git repo with a commit."""
    await run_git(["init"], path)
    
    # Configure user for commit
    await run_git(["config", "user.email", "test@test.com"], path)
    await run_git(["config", "user.name", "Test"], path)
    
    # Add files
    (path / "README.md").write_text("# Test Repo", encoding="utf-8")
    
    await run_git(["add", "."], path)
    await run_git(["commit", "-m", "Initial"], path)

@pytest.mark.asyncio
async def test_git_source_clone_and_fetch(temp_dirs):
    origin, cache = temp_dirs
    
    # Setup origin repo
    await init_git_repo(origin)
    
    # Initialize Source with custom cache
    source = GitContextSource(cache_dir=cache)
    
    # URI pointing to local origin (git supports file://)
    # normalization logic in GitContextSource prefixes https:// if git:// starts.
    # But if we pass file:// directly?
    # _normalize_url checks startsWith git://. If not, returns as is.
    # So we can use file:// URI.
    
    uri = f"file://{origin}"
    
    # Use query.path to fetch README.md
    # GitContextSource uses LocalContextSource on the cloned repo.
    # So we expect ContextItem from README.md
    
    query = ContextQuery(uri=uri, parameters={"path": "README.md"})
    
    items = await source.fetch(uri, query)
    
    assert len(items) == 1
    assert items[0].id == "README.md"
    assert "# Test Repo" in items[0].content
    
    # Verify it was cached
    repo_name = origin.name # "origin"
    # Actually _get_repo_name splits by /
    # url = file:///.../origin
    # repo name should be origin
    assert (cache / "origin").exists()

@pytest.mark.asyncio
async def test_git_source_pull_update(temp_dirs):
    origin, cache = temp_dirs
    await init_git_repo(origin)
    
    source = GitContextSource(cache_dir=cache)
    uri = f"file://{origin}"
    
    # 1. First fetch (Clone)
    await source.fetch(uri, ContextQuery(uri=uri))
    
    # 2. Update origin
    (origin / "new_file.txt").write_text("New Data")
    await asyncio.create_subprocess_exec("git", "add", ".", cwd=origin)
    await asyncio.create_subprocess_exec("git", "commit", "-m", "Update", cwd=origin)
    
    # 3. Second fetch (Pull)
    # We ask for the new file
    query = ContextQuery(uri=uri, parameters={"path": "new_file.txt"})
    items = await source.fetch(uri, query)
    
    assert len(items) == 1
    assert items[0].content == "New Data"
