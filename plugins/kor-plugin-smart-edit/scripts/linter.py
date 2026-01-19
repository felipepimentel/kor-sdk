import subprocess
import json
import logging
from typing import List, NamedTuple
from pathlib import Path
import ast

logger = logging.getLogger(__name__)

class LintError(NamedTuple):
    file: str
    line: int
    column: int
    message: str
    code: str

class LinterInterface:
    def check(self, file_path: Path) -> List[LintError]:
        raise NotImplementedError

class PythonSyntaxLinter(LinterInterface):
    """Basic syntax checker using AST."""
    def check(self, file_path: Path) -> List[LintError]:
        errors = []
        try:
            with open(file_path, "r") as f:
                source = f.read()
            ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            errors.append(LintError(
                file=str(file_path),
                line=e.lineno or 0,
                column=e.offset or 0,
                message=e.msg,
                code="SyntaxError"
            ))
        except Exception as e:
            errors.append(LintError(
                file=str(file_path),
                line=0,
                column=0,
                message=str(e),
                code="Unknown"
            ))
        return errors

class RuffLinter(LinterInterface):
    """Uses 'ruff' CLI tool."""
    def check(self, file_path: Path) -> List[LintError]:
        # Check if ruff is installed?
        # We assume yes for now or fallback
        cmd = ["ruff", "check", "--output-format=json", str(file_path)]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Ruff returns exit code 0 if no errors, 1 if errors. 
            # But we care about output.
            output = result.stdout
            if not output:
                 return []
            
            data = json.loads(output)
            errors = []
            for item in data:
                 errors.append(LintError(
                     file=item.get("filename", str(file_path)),
                     line=item.get("location", {}).get("row", 0),
                     column=item.get("location", {}).get("column", 0),
                     message=item.get("message", "Error"),
                     code=item.get("code", "Ruff")
                 ))
            return errors
        except FileNotFoundError:
             logger.warning("Ruff not found. Falling back to syntax check behavior (returning empty valid list if safe, or None?)")
             return []
        except json.JSONDecodeError:
             logger.error(f"Failed to parse ruff output: {result.stdout}")
             return []

class LinterService:
    def __init__(self):
        self.ruff = RuffLinter()
        self.syntax = PythonSyntaxLinter()

    def check(self, file_path: Path) -> List[LintError]:
        # Priority: Ruff
        # If ruff fails to run (not installed), fallback?
        # For now, let's chain them.
        
        # Check syntax first (fastest, most critical)
        syntax_errors = self.syntax.check(file_path)
        if syntax_errors:
            return syntax_errors
            
        # Then ruff
        return self.ruff.check(file_path)
