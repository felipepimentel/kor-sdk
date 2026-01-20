"""
Standard Context Sources (Adapters).
"""
import os
import logging
import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

from .protocols import ContextSourceProtocol
from .models import ContextQuery, ContextItem
from .exceptions import SourceError

logger = logging.getLogger(__name__)

class LocalContextSource:
    """
    Context Source for local filesystem.
    Config:
        root_dir: Base directory (default: cwd)
    """
    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path.cwd()

    async def fetch(self, uri: str, query: ContextQuery) -> List[ContextItem]:
        # uri format: local:///path/to/file or local:relative/path
        # parse path
        path_str = uri.replace("local://", "").replace("local:", "")
        path = self.root_dir / path_str
        
        if not path.exists():
            # Try user home if relative to home? No, let's stick to root_dir
            # Check if absolute path
            path = Path(path_str)
            if not path.exists():
                logger.warning(f"Local source path not found: {path}")
                return []

        items = []
        if path.is_file():
            items.append(self._read_file(path))
        elif path.is_dir():
             # Recursive? Maybe limit depth or check query params
             # For now, non-recursive listing of relevant files
             for child in path.iterdir():
                 if child.is_file():
                     try:
                        items.append(self._read_file(child))
                     except Exception:
                         pass # ignore binary or unreadable
        return items

    def _read_file(self, path: Path) -> ContextItem:
        try:
            content = path.read_text(encoding="utf-8")
            return ContextItem(
                id=path.name,
                content=content,
                source_uri=f"local://{path}",
                metadata={"type": "file", "path": str(path)}
            )
        except Exception as e:
            raise SourceError(f"Failed to read local file {path}: {e}")

    async def validate(self, config: Dict[str, Any]) -> bool:
        return True


class GitContextSource:
    """
    Context Source for Git repositories.
    Uses subprocess to clone/pull.
    """
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (Path.home() / ".kor" / "cache" / "git")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def fetch(self, uri: str, query: ContextQuery) -> List[ContextItem]:
        # uri format: git://github.com/org/repo or https://github.com/org/repo.git
        # We need to map URI to a cache location.
        # If uri starts with git://, it might be git protocol or just our scheme.
        repo_url = self._normalize_url(uri)
        repo_name = self._get_repo_name(repo_url)
        repo_path = self.cache_dir / repo_name
        
        # Clone or Pull
        if not repo_path.exists():
            await self._clone_repo(repo_url, repo_path)
        else:
            await self._pull_repo(repo_path)
            
        # Read content based on query parameters (e.g., file path, glob)
        # Default: Read README.md or explicitly requested path in query?
        # If query has 'path', use it.
        # If query is empty, maybe return README?
        
        target_path = repo_path
        subpath = query.parameters.get("path")
        if subpath:
            target_path = repo_path / subpath
            
        local_source = LocalContextSource(root_dir=repo_path)
        # Construct a local URI for the fetch
        local_uri = f"local:{subpath}" if subpath else f"local:."
        
        return await local_source.fetch(local_uri, query)

    def _normalize_url(self, uri: str) -> str:
        if uri.startswith("git://"):
            # If it's github, maybe map to https? 
            # Or assume user has ssh keys if using git@
            # For this MVP, let's treat git:// as a scheme token, and extract the real URL.
            # E.g. git://github.com/org/repo -> https://github.com/org/repo.git
            # Or git://git@github.com:org/repo -> git@github.com:org/repo
            suffix = uri.replace("git://", "")
            if "@" in suffix: # SSH
                 return suffix
            return f"https://{suffix}"
        return uri

    def _get_repo_name(self, url: str) -> str:
        # crude slug
        return url.split("/")[-1].replace(".git", "")

    async def _run_git(self, args: List[str], cwd: Path):
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise SourceError(f"Git command failed: {stderr.decode()}")

    async def _clone_repo(self, url: str, path: Path):
        logger.info(f"Cloning {url} to {path}")
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        # We run from parent
        await self._run_git(["clone", url, path.name], parent)

    async def _pull_repo(self, path: Path):
        logger.debug(f"Pulling {path}")
        await self._run_git(["pull"], path)

    async def validate(self, config: Dict[str, Any]) -> bool:
        return True
