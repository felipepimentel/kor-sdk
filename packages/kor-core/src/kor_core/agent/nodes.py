from typing import Dict, Any, Literal
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from .state import AgentState

# --- Supervisor Node ---
# Routes the conversation to the appropriate worker or finishes.

members = ["Coder", "Researcher"]
system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    " following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)

options = ["FINISH"] + members

# Using a lightweight check for keys (assuming env var is set or handled)
# For now, we'll try to initialize, but might need error handling if no key
try:
    llm = ChatOpenAI(model="gpt-4-turbo-preview")
except Exception:
    # Fallback or Mock for now if no key is present during dev
    llm = None 

def supervisor_node(state: AgentState):
    """
    Decides which worker should act next.
    """
    # Mock routing if no LLM (for testing without API Key)
    if not llm:
        last_msg = state['messages'][-1].content.lower()
        if "code" in last_msg:
            return {"next_step": "Coder"}
        elif "research" in last_msg:
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
# Simple Stubs for now

def coder_node(state: AgentState):
    return {
        "messages": [
            HumanMessage(content="[Coder] I am writing code for you...", name="Coder")
        ]
    }

def researcher_node(state: AgentState):
    return {
        "messages": [
            HumanMessage(content="[Researcher] I am searching the web...", name="Researcher")
        ]
    }
