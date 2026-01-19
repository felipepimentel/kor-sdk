from typing import Union, Dict, Any
from langchain_core.messages import HumanMessage
from .graph import create_graph

class GraphRunner:
    def __init__(self, graph=None):
        self.graph = graph or create_graph()

    def run(self, user_input: Union[str, Dict[str, Any]], thread_id: str = "default"):
        """
        Runs the graph with the user input and yields events.
        """
        from ..kernel import get_kernel
        from ..events.hook import HookEvent
        kernel = get_kernel()
        
        # Emit Agent Start
        # If input is complex, we just stringify for the hook
        hook_input = user_input if isinstance(user_input, str) else str(user_input)
        kernel.hooks.emit_sync(HookEvent.ON_AGENT_START, input=hook_input, thread_id=thread_id)

        if isinstance(user_input, str):
            inputs = {"messages": [HumanMessage(content=user_input)]}
        else:
            inputs = user_input
            
        config = {"configurable": {"thread_id": thread_id}}
        
        for event in self.graph.stream(inputs, config=config):
            # Emit Node Start for nodes in the event
            for node_name in event.keys():
                kernel.hooks.emit_sync(HookEvent.ON_NODE_START, node=node_name)
            
            yield event

        # Emit Agent End
        kernel.hooks.emit_sync(HookEvent.ON_AGENT_END, thread_id=thread_id)

