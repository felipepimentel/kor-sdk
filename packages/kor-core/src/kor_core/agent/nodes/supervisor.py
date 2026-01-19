from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from ...prompts import PromptLoader
from ...kernel import get_kernel
from ..state import AgentState

# Load prompt template once
system_prompt_template = PromptLoader.load("supervisor") or (
    "You are a supervisor tasked with managing a conversation between the"
    " following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results and status. When finished,"
    " respond with FINISH."
)

def supervisor_node(state: AgentState):
    """Decides which worker should act next."""
    kernel = get_kernel()
    
    # Get dynamic members from config
    members = kernel.config.agent.supervisor_members or ["Architect", "Coder", "Reviewer", "Researcher", "Explorer"]
    options = ["FINISH"] + members
    
    try:
        llm = kernel.model_selector.get_model("supervisor")
    except Exception:
        llm = None
    
    if not llm:
        # Fallback logic for basic tests if no LLM configured
        last_msg_obj = state['messages'][-1]
        if hasattr(last_msg_obj, "name") and last_msg_obj.name in members:
             return {"next_step": "FINISH"}

        last_msg = last_msg_obj.content.lower()
        if "create" in last_msg or "design" in last_msg:
             return {"next_step": "Architect"} if "Architect" in members else {"next_step": "Coder"}
        if "code" in last_msg or "file" in last_msg:
             return {"next_step": "Coder"} if "Coder" in members else {"next_step": "FINISH"}
        
        return {"next_step": "FINISH"}

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_template),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Given the conversation above, who should act next?"
            " Or should we FINISH? Select one of: {options}",
        ),
    ]).partial(options=str(options), members=", ".join(members))

    schema = {
        "name": "route",
        "description": "Select the next worker or FINISH",
        "parameters": {
            "type": "object",
            "properties": {
                "next": {"type": "string", "enum": options}
            },
            "required": ["next"]
        }
    }

    supervisor_chain = prompt | llm.with_structured_output(schema)
    return supervisor_chain.invoke(state)
