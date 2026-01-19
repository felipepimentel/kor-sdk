"""
Validation Module for LSP Integration

Provides validation capabilities for files using language-specific tools.
This module integrates with the LSP subsystem to provide code quality feedback.

Includes:
- Diagnostic: Single diagnostic message
- ValidationResult: Result of validation
- BaseValidator: Abstract validator interface
- CommandValidator: Executes external commands for validation
- LanguageRegistry: Maps file extensions to appropriate validators
"""

import asyncio
import json
import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from ..config import LanguageConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

class Diagnostic(BaseModel):
    """A single diagnostic message from validation."""
    file: str
    line: int
    message: str
    severity: str = "error"  # error, warning, info
    code: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of validating a file."""
    valid: bool
    diagnostics: List[Diagnostic] = Field(default_factory=list)
    raw_output: str = ""


# =============================================================================
# Validators
# =============================================================================

class BaseValidator(ABC):
    """Abstract base class for validators."""
    
    @abstractmethod
    async def validate(self, file_path: Path) -> ValidationResult:
        """Validate a file and return the result."""
        pass


class CommandValidator(BaseValidator):
    """
    Validator that executes an external command for validation.
    
    Supports JSON output formats from tools like Pyright, Ruff, etc.
    """
    
    def __init__(self, command: str, args: List[str], output_format: str = "json"):
        """
        Initialize the CommandValidator.
        
        Args:
            command: The command to execute (e.g., 'pyright', 'ruff')
            args: Arguments to pass to the command
            output_format: Expected output format ('json' or 'text')
        """
        self.command = command
        self.args = args
        self.output_format = output_format

    async def validate(self, file_path: Path) -> ValidationResult:
        """
        Runs the validation command on the file.
        """
        if not shutil.which(self.command):
            return ValidationResult(valid=False, raw_output=f"Tool not found: {self.command}")

        # Construct command
        # {file} is a placeholder, otherwise append to end
        final_args = []
        file_in_args = False
        for arg in self.args:
            if "{file}" in arg:
                final_args.append(arg.replace("{file}", str(file_path)))
                file_in_args = True
            else:
                final_args.append(arg)
        
        if not file_in_args:
            final_args.append(str(file_path))

        logger.debug(f"Running validator: {self.command} {final_args}")

        try:
            proc = await asyncio.create_subprocess_exec(
                self.command, *final_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode().strip() or stderr.decode().strip()
            
            diagnostics = self._parse_output(output)
            valid = len(diagnostics) == 0
            
            return ValidationResult(valid=valid, diagnostics=diagnostics, raw_output=output)

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(valid=False, raw_output=str(e))

    def _parse_output(self, output: str) -> List[Diagnostic]:
        """Parse validation command output into diagnostics."""
        diagnostics = []
        
        if not output:
            return diagnostics

        if self.output_format == "json":
            try:
                data = json.loads(output)
                # Pyright JSON structure
                if isinstance(data, dict) and "generalDiagnostics" in data:
                    for d in data["generalDiagnostics"]:
                        diagnostics.append(Diagnostic(
                            file=d.get("file", ""),
                            line=d.get("range", {}).get("start", {}).get("line", 0) + 1,
                            message=d.get("message", ""),
                            severity=d.get("severity", "error"),
                            code=d.get("rule", None)
                        ))
                # Ruff JSON structure (List of dicts)
                elif isinstance(data, list):
                    for d in data:
                        if "location" in d and "message" in d:
                            diagnostics.append(Diagnostic(
                                file=d.get("filename", ""),
                                line=d.get("location", {}).get("row", 0),
                                message=d.get("message", ""),
                                severity="error",
                                code=d.get("code")
                            ))
            except json.JSONDecodeError:
                pass

        elif self.output_format == "text":
            # Generic Text Parser - to be implemented when needed
            pass
            
        return diagnostics


# =============================================================================
# Language Registry
# =============================================================================

class LanguageRegistry:
    """
    Manages language configurations and returns appropriate validators.
    
    Maps file extensions to validators based on the KOR configuration.
    """
    
    def __init__(self, config: Dict[str, 'LanguageConfig']):
        """
        Initialize the LanguageRegistry.
        
        Args:
            config: Dictionary mapping language names to LanguageConfig objects
        """
        self.config = config
        self._cache_validators: Dict[str, BaseValidator] = {}
        
    def get_validator(self, file_path: str) -> Optional[BaseValidator]:
        """
        Determines the correct validator for a file based on extension.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            BaseValidator instance or None if no validator found
        """
        ext = "." + file_path.split(".")[-1] if "." in file_path else ""
        
        for lang_name, lang_config in self.config.items():
            if ext in lang_config.extensions:
                if lang_config.validator:
                    return self._get_or_create_validator(lang_name, lang_config.validator)
        
        return None

    def _get_or_create_validator(self, lang_name: str, val_config) -> BaseValidator:
        """Get cached validator or create new one."""
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
        
        Args:
            files: List of file paths to validate
            
        Returns:
            List of formatted error messages
        """
        feedback = []
        
        for f in files:
            path = Path(f)
            if not path.exists():
                continue
                
            validator = self.get_validator(f)
            if validator:
                res = await validator.validate(path)
                if not res.valid:
                    feedback.append(f"File: {f}\nErrors:\n{res.diagnostics or res.raw_output}")
                    
        return feedback


__all__ = [
    "Diagnostic",
    "ValidationResult", 
    "BaseValidator",
    "CommandValidator",
    "LanguageRegistry"
]
