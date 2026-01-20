import asyncio
import os
import shutil
from pathlib import Path
from kor_core.kernel import Kernel
from kor_core.context import ContextQuery

async def verify():
    print(" Booting Kernel...")
    async with Kernel() as kernel:
        cm = kernel.registry.get_service("context")
        print(" Context Manager retrieved from Registry.")
        
        # Test 1: Local Resolution (Default registered)
        test_file = Path("test_context.txt")
        test_file.write_text("Context Platform is working!", encoding="utf-8")
        
        try:
            print(f" Resolving local://{test_file} ...")
            result = await cm.resolve(f"local://{test_file}")
            content = result.items[0].content
            
            if "Context Platform is working!" in content:
                print(" SUCCESS: Local resolution worked.")
            else:
                print(f" FAILURE: Content mismatch: {content}")
                
        finally:
            if test_file.exists():
                test_file.unlink()
                
        # Test 2: Script Resolution (Default registered)
        print(" Testing Script Resolution...")
        
        script_file = Path("echo_test.py")
        script_file.write_text("print('Hello Script Resolved')")
        
        try:
            result = await cm.resolve(f"run:{script_file}")
            content = result.items[0].content
            if "Hello Script Resolved" in content:
                 print(" SUCCESS: Script resolution worked.")
            else:
                 print(f" FAILURE: Script content mismatch: {content}")
        finally:
            if script_file.exists():
                script_file.unlink()

if __name__ == "__main__":
    asyncio.run(verify())
