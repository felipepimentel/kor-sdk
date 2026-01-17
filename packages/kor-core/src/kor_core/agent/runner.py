from langchain_core.messages import HumanMessage
from .graph import create_graph

class GraphRunner:
    def __init__(self):
        self.graph = create_graph()

    def run(self, user_input: str):
        """
        Runs the graph with the user input and yields events.
        """
        inputs = {"messages": [HumanMessage(content=user_input)]}
        return self.graph.stream(inputs)
