"""
Verify Conversation Persistence using SQLite.
"""
from kor_core.agent.persistence import get_sqlite_checkpointer
from kor_core.agent.graph import create_graph
from kor_core import GraphRunner
from langchain_core.messages import HumanMessage

from unittest.mock import patch, MagicMock

def test_persistence():
    print("Testing Persistence...")
    checkpointer = get_sqlite_checkpointer()
    
    thread_id = "test-session-123"
    
    # Mocking the supervisor node directly in the graph execution
    # to avoid LLM complexity during persistence test
    with patch("kor_core.agent.graph.supervisor_node") as mock_sup:
        # 1. Create Graph and Runner inside patch
        graph = create_graph(checkpointer=checkpointer)
        runner = GraphRunner(graph=graph)

        # Turn 1: Route to Researcher then FINISH (via side_effect)
        mock_sup.side_effect = [
            {"next_step": "Researcher"},
            {"next_step": "FINISH"}
        ]
        
        print("Turn 1: Telling agent my name...")
        for event in runner.run("Hello, my name is Kor-Tester.", thread_id=thread_id):
            pass
            
        print("Restarting runner...")
        checkpointer2 = get_sqlite_checkpointer()
        # 2. Re-instantiate everything inside patch
        graph2 = create_graph(checkpointer=checkpointer2)
        runner2 = GraphRunner(graph=graph2)
        
        # Turn 2: Route to Researcher then FINISH
        mock_sup.side_effect = [
            {"next_step": "Researcher"},
            {"next_step": "FINISH"}
        ]
        
        print("Turn 2: Asking agent for my name...")
        for event in runner2.run("Do you remember my name?", thread_id=thread_id):
            pass

        # Verify state history in checkpointer
        state = graph2.get_state({"configurable": {"thread_id": thread_id}})
        history = state.values.get("messages", [])
        print(f"History length: {len(history)}")
        
        # History should have messages from both turns
        # Turn 1: Human, Supervisor (logic), Researcher, Supervisor (finish) -> 4 msgs?
        # Turn 2: Human, Supervisor, Researcher, Supervisor -> 4 msgs?
        
        has_name = any("Kor-Tester" in getattr(m, "content", "") for m in history)
        
        if has_name and len(history) >= 4:
            print(f"SUCCESS: Persistence is working! History has {len(history)} messages and remembers 'Kor-Tester'.")
        else:
            print(f"FAILURE: History check failed. Length: {len(history)}, Name found: {has_name}")

if __name__ == "__main__":
    test_persistence()
