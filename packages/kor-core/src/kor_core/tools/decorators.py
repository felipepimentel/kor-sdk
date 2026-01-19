from typing import Callable, Type, Optional, List
from pydantic import BaseModel, Field, create_model
import inspect
from .base import KorTool

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    auto_register: bool = False,
    tags: Optional[List[str]] = None,
):
    """
    Decorator to create a KOR tool from a function.
    
    Usage:
        @tool
        def my_tool(query: str) -> str:
            '''Does something amazing.'''
            return "result"
    
        @tool(name="custom_name", description="Custom description")
        def another_tool(x: int) -> int:
            return x * 2
    """
    def decorator(func: Callable) -> Type[KorTool]:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or "No description"
        
        # Build args schema from function signature
        sig = inspect.signature(func)
        fields = {}
        for param_name, param in sig.parameters.items():
            annotation = param.annotation if param.annotation != inspect.Parameter.empty else str
            default = param.default if param.default != inspect.Parameter.empty else ...
            fields[param_name] = (annotation, Field(default=default))
        
        ArgsSchema = create_model(f"{tool_name.capitalize()}Input", **fields)
        
        class DynamicTool(KorTool):
            name: str = tool_name
            description: str = tool_description
            args_schema: Type[BaseModel] = ArgsSchema
            
            def _run(self, **kwargs) -> str:
                return str(func(**kwargs))
        
        DynamicTool.__name__ = f"{tool_name.capitalize()}Tool"
        
        if auto_register:
            from ..kernel import get_kernel
            try:
                kernel = get_kernel()
                registry = kernel.registry.get_service("tools")
                if registry:
                    registry.register(DynamicTool(), tags=tags)
            except Exception:
                # Kernel might not be initialized or registry service missing
                pass
                
        return DynamicTool
    
    # Handle @tool vs @tool() usage
    if callable(name):
        func = name
        name = None
        return decorator(func)
    
    return decorator
