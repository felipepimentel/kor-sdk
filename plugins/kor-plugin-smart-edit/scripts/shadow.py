import shutil
import os
import tempfile
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class ShadowWorkspace:
    """
    Manages a shadow copy of files for safe editing.
    """
    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir:
            self.shadow_dir = base_dir
        else:
             # Use a persistent temp dir so we can debug if needed, or unique per session
            self.shadow_dir = Path(tempfile.gettempdir()) / "kor_shadow"
        
        self.shadow_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Shadow workspace initialized at {self.shadow_dir}")

    def create_shadow_file(self, original_path: Path) -> Path:
        """
        Creates a copy of the original file in the shadow workspace.
        Returns the path to the shadow file.
        """
        original_path = original_path.resolve()
        
        # Create a unique path inside shadow dir based on original path to avoid collisions
        # e.g. /tmp/kor_shadow/home/user/project/file.py
        # We strip the anchor (root) from original path
        relative_path = original_path.relative_to(original_path.anchor) 
        shadow_path = self.shadow_dir / relative_path
        
        shadow_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original_path, shadow_path)
        
        return shadow_path

    def update_content(self, shadow_path: Path, new_content: str) -> None:
        """
        Overwrites the shadow file with new content.
        """
        with open(shadow_path, "w") as f:
            f.write(new_content)

    def commit(self, shadow_path: Path, original_path: Path) -> None:
        """
        Moves the shadow file content to the original path.
        """
        # We read from shadow and write to original to preserve original file metadata/permissions if possible,
        # or just move. shutil.move replaces metadata.
        # Safe strategy: Copy content
        shutil.copy2(shadow_path, original_path)
        logger.info(f"Committed shadow {shadow_path} to {original_path}")

    def cleanup(self):
        """Removes the shadow directory."""
        shutil.rmtree(self.shadow_dir, ignore_errors=True)
