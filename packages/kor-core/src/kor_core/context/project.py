import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ProjectContextDetector:
    """
    Detects standard project context structure (`.agent/` directory)
    and generates default context mappings.
    """
    
    AGENT_DIR = ".agent"
    
    # Standard aliases to look for
    ALIASES = {
        "project:root": ".",        # Mapped to .agent/
        "project:agent": "AGENTS.md",
        "project:rules": "rules.md",
        "project:memory": "memories",
        "project:skills": "skills",
    }
    
    # Fallback/Alternative filenames
    ALTERNATIVES = {
        "project:agent": ["AGENT.md", "agent.md", "agents.md"],
    }
    
    @classmethod
    def detect(cls, root_dir: Path = None) -> Dict[str, str]:
        """
        Scan the project directory for standard context files.
        
        Args:
            root_dir: The root directory to start searching from. 
                      Defaults to current working directory.
                      
        Returns:
            Dictionary of context mappings (alias -> URI).
        """
        if root_dir is None:
            root_dir = Path.cwd()
            
        agent_dir = root_dir / cls.AGENT_DIR
        mappings: Dict[str, str] = {}
        
        if not agent_dir.exists():
            logger.debug(f"No {cls.AGENT_DIR} directory found in {root_dir}")
            return mappings
            
        logger.info(f"Detected project context in {agent_dir}")
        
        # 1. Project Root
        mappings["project:root"] = f"local://{cls.AGENT_DIR}/"
        
        # 2. Check for standard files
        for alias, relative_path in cls.ALIASES.items():
            if alias == "project:root":
                continue
                
            # Check detection logic
            target_path = agent_dir / relative_path
            
            # Check alternatives if main one doesn't exist
            found_path = None
            if target_path.exists():
                found_path = relative_path
            elif alias in cls.ALTERNATIVES:
                for alt in cls.ALTERNATIVES[alias]:
                    alt_path = agent_dir / alt
                    if alt_path.exists():
                        found_path = alt
                        break
            
            if found_path:
                # Create local:// URI relative to CWD (so includes .agent/)
                uri_path = f"{cls.AGENT_DIR}/{found_path}"
                mappings[alias] = f"local://{uri_path}"
                logger.debug(f"  Detected {alias} -> {mappings[alias]}")
                
        return mappings

