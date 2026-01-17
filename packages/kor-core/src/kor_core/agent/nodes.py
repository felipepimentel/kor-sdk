from typing import Dict, Any, Literal
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from .state import AgentState
from ..tools.terminal import TerminalTool
from ..tools.browser import BrowserTool

# --- Supervisor Node ---
members = ["Coder", "Researcher"]
system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    " following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)

options = ["FINISH"] + members

try:
    llm = ChatOpenAI(model="gpt-4-turbo-preview")
except Exception:
    llm = None 

def supervisor_node(state: AgentState):
    """Decides which worker should act next."""
    if not llm:
        last_msg = state['messages'][-1].content.lower()
        if "code" in last_msg or "file" in last_msg or "list" in last_msg:
            return {"next_step": "Coder"}
        elif "research" in last_msg or "search" in last_msg or "web" in last_msg:
            return {"next_step": "Researcher"}
        return {"next_step": "FINISH"}

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), members=", ".join(members))

    supervisor_chain = (
        prompt
        | llm.bind_functions(functions=[dict(name="route", parameters=dict(type="object", properties=dict(next=dict(type="string", enum=options)), required=["next"]))], function_call="route")
        | JsonOutputFunctionsParser()
    )

    return supervisor_chain.invoke(state)

# --- Worker Nodes ---

def coder_node(state: AgentState):
    """
    Coder Worker. Can execute terminal commands.
    """
    # Simple logic: If the user message asks to list files, we do it.
    last_msg = state['messages'][-1].content
    tool = TerminalTool()
    
    response = "I am ready to code."
    
    # Very naive instruction following for V1
    if "list" in last_msg.lower():
        output = tool._run("ls -la")
        response = f"Listing files:\n{output}"
    
    return {
        "messages": [
            HumanMessage(content=f"[Coder] {response}", name="Coder")
        ]
    }

def researcher_node(state: AgentState):
    """
    Researcher Worker. Can search the web.
    """
    tool = BrowserTool()
    last_msg = state['messages'][-1].content
    
    response = "I am ready to research."
    # Naive extraction (in real world an Agent would decide arguments)
    if "search" in last_msg.lower() or "research" in last_msg.lower():
        # Strip "search"
        query = last_msg.replace("search", "").replace("research", "").strip() or "python mcp"
        output = tool._run(query)
        response = f"Search Results for '{query}':\n{output}"

    return {
        "messages": [
            HumanMessage(content=f"[Researcher] {response}", name="Researcher")
        ]
    }
