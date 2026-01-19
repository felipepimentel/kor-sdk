from typing import Optional, List, Dict
import logging
from .validator import CommandValidator, BaseValidator

logger = logging.getLogger(__name__)

class LanguageRegistry:
    """
    Manages language configurations and returns appropriate validators.
    """
    def __init__(self, config: Dict[str, 'LanguageConfig']):
        self.config = config
        self._cache_validators: Dict[str, BaseValidator] = {}
        
    def get_validator(self, file_path: str) -> Optional[BaseValidator]:
        """
        Determines the correct validator for a file based on extension.
        """
        ext = "." + file_path.split(".")[-1] if "." in file_path else ""
        
        # Simple lookup
        for lang_name, lang_config in self.config.items():
            if ext in lang_config.extensions:
                # Found language match
                if lang_config.validator:
                    return self._get_or_create_validator(lang_name, lang_config.validator)
        
        return None

    def _get_or_create_validator(self, lang_name: str, val_config) -> BaseValidator:
        key = f"{lang_name}_validator"
        if key in self._cache_validators:
            return self._cache_validators[key]
        
        validator = CommandValidator(
            command=val_config.command,
            args=val_config.args,
            output_format=val_config.format
        )
        self._cache_validators[key] = validator
        return validator

    async def validate_files(self, files: List[str]) -> List[str]:
        """
        Validates a batch of files and returns formatted error strings.
        """
        from pathlib import Path
        feedback = []
        
        for f in files:
            path = Path(f)
            if not path.exists():
                continue
                
            validator = self.get_validator(f)
            if validator:
                # logger.debug(f"Validating {f} with {validator.command}...")
                res = await validator.validate(path)
                if not res.valid:
                    feedback.append(f"File: {f}\nErrors:\n{res.diagnostics or res.raw_output}")
                    
        return feedback
