from langchain_core.messages import HumanMessage
from .graph import create_graph

class GraphRunner:
    def __init__(self, graph=None):
        self.graph = graph or create_graph()

    def run(self, user_input: str, thread_id: str = "default"):
        """
        Runs the graph with the user input and yields events.
        """
        from ..kernel import get_kernel
        from ..events.hook import HookEvent
        kernel = get_kernel()
        
        # Emit Agent Start
        kernel.hooks.emit_sync(HookEvent.ON_AGENT_START, input=user_input, thread_id=thread_id)

        inputs = {"messages": [HumanMessage(content=user_input)]}
        config = {"configurable": {"thread_id": thread_id}}
        
        for event in self.graph.stream(inputs, config=config):
            # Emit Node Start for nodes in the event
            for node_name in event.keys():
                kernel.hooks.emit_sync(HookEvent.ON_NODE_START, node=node_name)
            
            yield event

        # Emit Agent End
        kernel.hooks.emit_sync(HookEvent.ON_AGENT_END, thread_id=thread_id)

