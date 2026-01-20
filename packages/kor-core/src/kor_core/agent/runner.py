from typing import Union, Dict, Any
from langchain_core.messages import HumanMessage
from .graph import create_graph

class GraphRunner:
    def __init__(self, graph=None):
        self.graph = graph or create_graph()

    async def run(self, user_input: Union[str, Dict[str, Any]], thread_id: str = "default"):
        """
        Runs the graph with the user input and yields events.
        """
        import uuid
        from ..kernel import get_kernel
        from ..events import HookEvent
        kernel = get_kernel()
        
        # Generate Trace ID for observability
        trace_id = str(uuid.uuid4())
        
        # Emit Agent Start (Async)
        hook_input = user_input if isinstance(user_input, str) else str(user_input)
        await kernel.hooks.emit(
            HookEvent.ON_AGENT_START, 
            input=hook_input, 
            thread_id=thread_id,
            trace_id=trace_id,
            agent_id="KOR-Agent"
        )

        if isinstance(user_input, str):
            inputs = {"messages": [HumanMessage(content=user_input)]}
        else:
            inputs = user_input
            
        config = {"configurable": {"thread_id": thread_id}}
        
        # stream is sync generator but we can wrap it if needed, 
        # or use astream if the graph supports it (LangGraph does).
        async for event in self.graph.astream(inputs, config=config):
            # Emit Node Start for nodes in the event
            for node_name in event.keys():
                await kernel.hooks.emit(
                    HookEvent.ON_NODE_START, 
                    node=node_name,
                    trace_id=trace_id,
                    parent_id=trace_id # Simplified for V1
                )
            
            yield event

        # Emit Agent End
        await kernel.hooks.emit(
            HookEvent.ON_AGENT_END, 
            thread_id=thread_id,
            trace_id=trace_id
        )

