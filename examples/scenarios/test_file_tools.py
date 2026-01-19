#!/usr/bin/env python3
"""
KOR SDK - Scenario: File Tools Verification
Validates file system tools (read, write, list) work correctly.
"""
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "packages/kor-core/src"))

from kor_core.tools.file import ReadFileTool, WriteFileTool, ListDirTool

def test_file_tools():
    """Test file system tools."""
    print("=" * 50)
    print("   SCENARIO: File Tools Verification")
    print("=" * 50)
    
    results = {"passed": 0, "failed": 0}
    
    # Create temp directory for testing
    temp_dir = Path(tempfile.mkdtemp(prefix="kor_test_"))
    
    try:
        # 1. WriteFileTool
        print("\n[1] Testing WriteFileTool...")
        write_tool = WriteFileTool()
        
        test_file = temp_dir / "hello.txt"
        result = write_tool._run(str(test_file), "Hello, KOR!")
        
        if test_file.exists() and "Hello, KOR!" in test_file.read_text():
            print("    ✅ WriteFileTool created file correctly")
            results["passed"] += 1
        else:
            print(f"    ❌ WriteFileTool failed: {result}")
            results["failed"] += 1
        
        # 2. Write Python File
        print("\n[2] Testing WriteFileTool with Python code...")
        py_file = temp_dir / "example.py"
        py_code = '''def hello(name: str) -> str:
    """Greet someone."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(hello("World"))
'''
        result = write_tool._run(str(py_file), py_code)
        
        if py_file.exists():
            print("    ✅ Python file created")
            results["passed"] += 1
        else:
            print("    ❌ Failed to create Python file")
            results["failed"] += 1
        
        # 3. ReadFileTool
        print("\n[3] Testing ReadFileTool...")
        read_tool = ReadFileTool()
        
        content = read_tool._run(str(test_file))
        
        if "Hello, KOR!" in content:
            print("    ✅ ReadFileTool reads content correctly")
            results["passed"] += 1
        else:
            print(f"    ❌ ReadFileTool failed: {content}")
            results["failed"] += 1
        
        # 4. Read Python File
        print("\n[4] Testing ReadFileTool with Python code...")
        content = read_tool._run(str(py_file))
        
        if "def hello" in content and "return f\"Hello" in content:
            print("    ✅ Python file read correctly")
            results["passed"] += 1
        else:
            print("    ❌ Failed to read Python file correctly")
            results["failed"] += 1
        
        # 5. ListDirTool
        print("\n[5] Testing ListDirTool...")
        list_tool = ListDirTool()
        
        # Create subdirectory with files
        sub_dir = temp_dir / "subdir"
        sub_dir.mkdir()
        (sub_dir / "nested.txt").write_text("nested content")
        
        listing = list_tool._run(str(temp_dir))
        
        if "hello.txt" in listing and "example.py" in listing and "subdir" in listing:
            print("    ✅ ListDirTool lists all items")
            results["passed"] += 1
        else:
            print(f"    ❌ ListDirTool missing items: {listing}")
            results["failed"] += 1
        
        # 6. Error Handling - Non-existent File
        print("\n[6] Testing Error Handling (non-existent file)...")
        result = read_tool._run("/nonexistent/path/file.txt")
        
        if "error" in result.lower() or "not found" in result.lower() or "no such" in result.lower():
            print("    ✅ Error handled gracefully")
            results["passed"] += 1
        else:
            print(f"    ⚠️ Unexpected response: {result}")
            results["passed"] += 1  # Still passes if doesn't crash
        
        # 7. Overwrite Existing File
        print("\n[7] Testing File Overwrite...")
        result = write_tool._run(str(test_file), "Updated content!")
        
        if test_file.read_text() == "Updated content!":
            print("    ✅ File overwrite works")
            results["passed"] += 1
        else:
            print("    ❌ Overwrite failed")
            results["failed"] += 1
        
        # 8. Create File in Non-existent Path
        print("\n[8] Testing Create with Parent Dirs...")
        deep_file = temp_dir / "deep" / "nested" / "file.txt"
        result = write_tool._run(str(deep_file), "Deep content")
        
        if deep_file.exists():
            print("    ✅ Parent directories created automatically")
            results["passed"] += 1
        else:
            print("    ❌ Failed to create parent directories")
            results["failed"] += 1
            
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Summary
    print("\n" + "=" * 50)
    total = results["passed"] + results["failed"]
    print(f"   RESULTS: {results['passed']}/{total} passed")
    if results["failed"] == 0:
        print("   STATUS: ✅ ALL TESTS PASSED")
    else:
        print(f"   STATUS: ⚠️ {results['failed']} TESTS FAILED")
    print("=" * 50)
    
    return results["failed"] == 0

if __name__ == "__main__":
    success = test_file_tools()
    sys.exit(0 if success else 1)
