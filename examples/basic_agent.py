"""
Basic Agent Example

Demonstrates how to use the KOR SDK to create and run a simple agent.
"""

from kor_core import Kernel, GraphRunner

def main():
    # 1. Initialize the Kernel
    kernel = Kernel()
    kernel.boot()
    
    print(f"Kernel booted. User: {kernel.config.user.name or 'Guest'}")
    
    # 2. Create a GraphRunner
    runner = GraphRunner()
    
    # 3. Run a query
    print("\n--- Running Agent ---")
    for event in runner.run("List the files in the current directory"):
        for node, details in event.items():
            print(f"[{node}] {details}")
    
    print("\n--- Done ---")

if __name__ == "__main__":
    main()
