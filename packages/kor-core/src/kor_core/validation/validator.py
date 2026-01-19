import asyncio
import json
import logging
import shutil
import tempfile
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class Diagnostic(BaseModel):
    file: str
    line: int
    message: str
    severity: str = "error" # error, warning, info
    code: Optional[str] = None

class ValidationResult(BaseModel):
    valid: bool
    diagnostics: List[Diagnostic] = Field(default_factory=list)
    raw_output: str = ""

class BaseValidator(ABC):
    @abstractmethod
    async def validate(self, file_path: Path) -> ValidationResult:
        pass

class CommandValidator(BaseValidator):
    def __init__(self, command: str, args: List[str], output_format: str = "json"):
        self.command = command
        self.args = args
        self.output_format = output_format

    async def validate(self, file_path: Path) -> ValidationResult:
        """
        Runs the validation command on the file.
        Uses a temporary directory to mimic compilation context if needed,
        or runs directly if the tool supports single files.
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
            
            # Non-zero exit usually means errors (or crash)
            # But some linters return 0 even with warnings.
            # We rely on parsing.
            
            diagnostics = self._parse_output(output)
            valid = len(diagnostics) == 0
            
            return ValidationResult(valid=valid, diagnostics=diagnostics, raw_output=output)

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(valid=False, raw_output=str(e))

    def _parse_output(self, output: str) -> List[Diagnostic]:
        diagnostics = []
        
        if not output:
            return diagnostics

        if self.output_format == "json":
            # Expects strict JSON definition of Tool Output? 
            # Or standard Pyright/LSP JSON?
            # For now, let's look at Pyright JSON format logic.
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
                        # Ruff: { "code": "F401", "message": "...", "location": { "row": 1, "column": 1 }, "filename": "..." }
                        if "location" in d and "message" in d:
                            diagnostics.append(Diagnostic(
                                file=d.get("filename", ""),
                                line=d.get("location", {}).get("row", 0),
                                message=d.get("message", ""),
                                severity="error", # Default to error
                                code=d.get("code")
                            ))
            except json.JSONDecodeError:
                pass # Fallback?

        elif self.output_format == "text":
            # Generic Text Parser (Line:Message)
            # Implemented as pass for now, will be implemented when needed.
            pass
            
        return diagnostics
