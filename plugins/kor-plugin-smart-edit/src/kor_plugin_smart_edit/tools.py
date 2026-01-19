from pathlib import Path
from typing import Type
from kor_core.tools import KorTool
from .shadow import ShadowWorkspace
from .linter import LinterService

class SmartEditTool(KorTool):
    name: str = "smart_edit"
    description: str = "Safely edits a file. Verifies changes with linters before committing. If errors occur, changes are discarded and errors returned."
    
    def _run(self, file_path: str, content: str) -> str:
        workspace = ShadowWorkspace()
        linter = LinterService()
        
        target = Path(file_path).resolve()
        if not target.exists():
            return f"Error: File {file_path} not found."
            
        try:
            # 1. Create Shadow
            shadow_file = workspace.create_shadow_file(target)
            
            # 2. Apply Edit
            workspace.update_content(shadow_file, content)
            
            # 3. Verify
            errors = linter.check(shadow_file)
            
            if errors:
                # Format errors for the agent
                error_msg = "Edit Rejected. Verification Failed:\n"
                for e in errors:
                    error_msg += f"- Line {e.line}: {e.message} ({e.code})\n"
                return error_msg
                
            # 4. Commit
            workspace.commit(shadow_file, target)
            return f"File {target.name} updated successfully and verified."
            
        except Exception as e:
            return f"Internal Error during Smart Edit: {e}"
        finally:
            workspace.cleanup()
