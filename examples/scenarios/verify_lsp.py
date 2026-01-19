import asyncio
import os
from pathlib import Path
from kor_core.kernel import get_kernel
from kor_core.tools.lsp import LSPHoverTool, LSPDefinitionTool

async def run_verification():
    print("--- Verifying LSP Tools ---")
    
    # 1. Setup Environment
    cwd = Path(os.getcwd())
    target_file = cwd / "examples" / "out" / "lsp_test.py"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a simple python file
    content = """
class DataProcessor:
    def process(self, data: str) -> int:
        \"\"\"Process the data and return an integer.\"\"\"
        return len(data)

dp = DataProcessor()
dp.process("hello")
"""
    target_file.write_text(content)
    print(f"Created test file: {target_file}")
    
    # 2. Boot Kernel
    kernel = get_kernel()
    kernel.boot()
    
    # 3. Get Tools
    hover_tool = LSPHoverTool()
    definition_tool = LSPDefinitionTool()
    
    # Allow LSP to initialize/analyze
    print("Waiting for LSP analysis...")
    await asyncio.sleep(2)
    
    # 4. Test Hover
    # Line 7: dp.process("hello")
    # 0123
    # dp.p
    # Position: Line 7, Col 4 (1-based) -> 'p'
    print("\n[Action] Hovering over 'process' at line 7, col 4...")
    hover_result = await hover_tool._arun(str(target_file), 7, 4)
    print(f"[Result] Hover:\n{hover_result}")
    
    if "process" in str(hover_result) or "Process the data" in str(hover_result):
        print("✅ Hover Verified")
    else:
        print("❌ Hover Failed")

    # 5. Test Definition
    print("\n[Action] Go to Definition of 'DataProcessor' at line 6...")
    # dp = DataProcessor() -> line 6
    def_result = await definition_tool._arun(str(target_file), 6, 10)
    print(f"[Result] Definition:\n{def_result}")
    
    # Expect line 2
    if ":2" in def_result:
        print("✅ Definition Verified")
    else:
        print("❌ Definition Failed")

    # 6. Cleanup
    await kernel.shutdown()

if __name__ == "__main__":
    asyncio.run(run_verification())
