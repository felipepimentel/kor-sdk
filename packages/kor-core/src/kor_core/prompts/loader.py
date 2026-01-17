"""
Loading prompts from files.
"""

from pathlib import Path
from importlib.resources import files
import os

from ..config import ConfigManager

class PromptLoader:
    """Methods to load prompts from the package or user override."""
    
    @staticmethod
    def load(name: str) -> str:
        """
        Loads a prompt by name (filename without extension).
        Priority:
        1. ~/.kor/prompts/{name}.md
        2. kor_core/prompts/{name}.md
        """
        filename = f"{name}.md"
        
        # 1. Check user override
        cm = ConfigManager()
        # Assumes config path structure ~/.kor/config.toml -> ~/.kor/prompts/
        user_prompts_dir = cm.config_path.parent / "prompts"
        user_file = user_prompts_dir / filename
        
        if user_file.exists():
            return user_file.read_text(encoding="utf-8")
            
        # 2. Check package resources
        # We assume prompts are in the 'kor_core.prompts' package
        try:
            # For python 3.10+ importlib.resources.files is preferred
            prompt_path = files("kor_core.prompts").joinpath(filename)
            if prompt_path.is_file():
                 return prompt_path.read_text(encoding="utf-8")
        except Exception as e:
            pass
            
        return ""
