from typing import Callable, Type, Optional, List
from pydantic import BaseModel, Field, create_model
import inspect
import asyncio
import warnings
from .base import KorTool

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    auto_register: bool = False,
    tags: Optional[List[str]] = None,
):
    """
    Decorator to create a KOR tool from a function.
    
    Supports both synchronous and asynchronous functions.
    
    Usage:
        @tool
        def my_tool(query: str) -> str:
            '''Does something amazing.'''
            return "result"
    
        @tool(name="custom_name", description="Custom description")
        async def async_tool(url: str) -> str:
            '''Fetches data asynchronously.'''
            return await fetch(url)
    """
    def decorator(func: Callable) -> Type[KorTool]:
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or "No description"
        is_async = asyncio.iscoroutinefunction(func)
        
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
                """Synchronous execution - handles both sync and async functions."""
                result = func(**kwargs)
                if asyncio.iscoroutine(result):
                    # Async function called from sync context
                    try:
                        loop = asyncio.get_running_loop()
                        # Already in async context - use nest_asyncio pattern or warn
                        warnings.warn(
                            f"Async tool '{tool_name}' called synchronously from async context. "
                            "Consider using _arun() instead."
                        )
                        import nest_asyncio
                        nest_asyncio.apply()
                        return str(loop.run_until_complete(result))
                    except RuntimeError:
                        # No running loop - safe to run
                        return str(asyncio.run(result))
                    except ImportError:
                        # nest_asyncio not installed
                        return str(asyncio.run(result))
                return str(result)
            
            async def _arun(self, **kwargs) -> str:
                """Asynchronous execution - handles both sync and async functions."""
                result = func(**kwargs)
                if asyncio.iscoroutine(result):
                    return str(await result)
                return str(result)
        
        DynamicTool.__name__ = f"{tool_name.capitalize()}Tool"
        
        if auto_register:
            from ..kernel import get_kernel
            try:
                kernel = get_kernel()
                registry = kernel.registry.get_service("tools")
                if registry:
                    registry.register(DynamicTool(), tags=tags)
            except Exception as e:
                warnings.warn(
                    f"Auto-registration of tool '{tool_name}' failed: {e}. "
                    "Tool will not be available until manually registered.",
                    RuntimeWarning
                )
                
        return DynamicTool
    
    # Handle @tool vs @tool() usage
    if callable(name):
        func = name
        name = None
        return decorator(func)
    
    return decorator

