"""
Prompts package.
"""

from importlib.resources import files
from pathlib import Path
from .config import ConfigManager

class PromptLoader:
    """Methods to load prompts from the package or user override."""
    
    @staticmethod
    def export_defaults():
        """Exports default prompts to user directory if they don't exist."""
        cm = ConfigManager()
        user_prompts_dir = cm.config_path.parent / "prompts"
        user_prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # List of core prompts to export
        core_prompts = ["supervisor"]
        
        for name in core_prompts:
            filename = f"{name}.md"
            user_file = user_prompts_dir / filename
            if not user_file.exists():
                content = PromptLoader.load(name, skip_user=True)
                if content:
                    user_file.write_text(content, encoding="utf-8")

    @staticmethod
    def load(name: str, skip_user: bool = False) -> str:
        """
        Loads a prompt by name (filename without extension).
        Priority:
        1. ~/.kor/prompts/{name}.md (if not skipped)
        2. kor_core/resources/prompts/{name}.md
        """
        filename = f"{name}.md"
        
        if not skip_user:
            # 1. Check user override
            cm = ConfigManager()
            user_prompts_dir = cm.config_path.parent / "prompts"
            user_file = user_prompts_dir / filename
            
            if user_file.exists():
                return user_file.read_text(encoding="utf-8")
            
        # 2. Check repository resources (Dev Mode)
        # Assuming layout: repo_root/resources/prompts/
        # kor_core/prompts.py is 5 levels deep in src layout
        try:
             repo_root = Path(__file__).parents[4] 
             resource_file = repo_root / "resources" / "prompts" / filename
             if resource_file.exists():
                 return resource_file.read_text(encoding="utf-8")
        except Exception:
             pass

        # 3. Fallback: Check standard package location (for installed wheels)
        # This requires RESOURCES to be included in package data, which user currently moved out.
        # We keep this as a placeholder or check a known install location.
        # For now, if we are installed, we might expect ~/.kor/prompts to be populated by `export_defaults`.
            
        return ""
