"""
Custom Tool Example

Demonstrates how to create custom tools using the @tool decorator.
"""

from kor_core import tool

@tool
def greet(name: str) -> str:
    """Greets a person by name."""
    return f"Hello, {name}! Welcome to KOR."

@tool(name="calculate", description="Performs basic arithmetic")
def calc(a: int, b: int, operation: str = "add") -> str:
    """Calculates a result based on the operation."""
    match operation:
        case "add":
            return str(a + b)
        case "subtract":
            return str(a - b)
        case "multiply":
            return str(a * b)
        case _:
            return "Unknown operation"

def main():
    # Create tool instances
    GreetTool = greet
    CalcTool = calc
    
    print("Created tools:")
    print(f"  - {GreetTool.name}: {GreetTool.description}")
    print(f"  - {CalcTool.name}: {CalcTool.description}")
    
    # Use the tools
    greet_instance = GreetTool()
    print(f"\n{greet_instance._run(name='Developer')}")
    
    calc_instance = CalcTool()
    print(f"2 + 3 = {calc_instance._run(a=2, b=3, operation='add')}")

if __name__ == "__main__":
    main()
