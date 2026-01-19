from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...prompts import PromptLoader
from ...kernel import get_kernel
from ..state import AgentState

def architect_node(state: AgentState):
    """Architect. Creates technical specs."""
    last_msg = state['messages'][-1].content
    kernel = get_kernel()
    
    system_prompt = PromptLoader.load("architect") or "You are an Architect. Create a spec for the user request."
    
    try:
        llm = kernel.model_selector.get_model("coding") 
    except Exception:
        spec = f"SPECIFICATION (Mock) for: {last_msg}\n1. Create component.\n2. Add props."
        return {
            "messages": [HumanMessage(content=f"[Architect] {spec}", name="Architect")],
            "spec": spec,
            "next_step": "Coder"
        }

    tool_names = ["search_symbols", "lsp_definition", "lsp_hover"]
    chain = (
        ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Tools Available: " + ", ".join(tool_names) + "\n\nRequest: {input}")
        ]) 
        | llm 
        | StrOutputParser()
    )
    
    try:
        spec = chain.invoke({"input": last_msg})
    except Exception as e:
        spec = f"Error generating spec: {e}"

    response = f"Created spec:\n{spec}"
    return {
        "messages": [HumanMessage(content=f"[Architect] {response}", name="Architect")],
        "spec": spec,
        "next_step": "Coder"
    }
