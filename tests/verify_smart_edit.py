import sys
from pathlib import Path

# Add plugin source to path
sys.path.insert(0, str(Path.cwd() / "plugins/kor-plugin-smart-edit/src"))

from kor_plugin_smart_edit.tools import SmartEditTool

def verify_smart_edit():
    target = Path("test_safe_edit.py")
    
    # 1. Setup
    print("[1] Creating initial file...")
    target.write_text("def hello():\n    print('Hello World')\n")
    original_content = target.read_text()
    
    tool = SmartEditTool()
    
    # 2. Try Bad Edit (Syntax Error)
    print("\n[2] Attempting BAD edit (Syntax Error)...")
    bad_content = "def hello()\n    print('Missing colon')" # Syntax error
    result = tool._run(str(target), bad_content)
    print(f"Result: {result}")
    
    if "Edit Rejected" in result and "SyntaxError" in result:
        print("✅ Correctly rejected bad code.")
    else:
        print("❌ FAIL: Did not reject bad code properly.")
        sys.exit(1)
        
    # Verify file wasn't touched
    if target.read_text() == original_content:
        print("✅ File content preserved (Safe).")
    else:
        print("❌ FAIL: File was modified despite error!")
        sys.exit(1)

    # 3. Try Good Edit
    print("\n[3] Attempting GOOD edit...")
    good_content = "def hello():\n    print('Hello Verified World')\n"
    result = tool._run(str(target), good_content)
    print(f"Result: {result}")
    
    if "updated successfully" in result:
        print("✅ Accepted valid code.")
    else:
        print(f"❌ FAIL: Rejected valid code. Result: {result}")
        sys.exit(1)
        
    if target.read_text() == good_content:
        print("✅ File content updated.")
    else:
        print("❌ FAIL: File content mismtach.")
        sys.exit(1)
        
    # Cleanup
    target.unlink()
    print("\n✅ Smart Edit Verification Passed!")

if __name__ == "__main__":
    verify_smart_edit()
