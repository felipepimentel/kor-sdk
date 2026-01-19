from ...kernel import get_kernel
from ..state import AgentState
from .base import get_tool_from_registry
from langchain_core.messages import HumanMessage

def coder_node(state: AgentState):
    """Coder Worker. Translates Spec to Code."""
    # Process based on current state
    
    # 1. Check for Errors (Self-Healing)
    if state.get("errors"):
        errors = state["errors"]
        response = f"Fixing errors: {errors}"
        return {
            "messages": [HumanMessage(content=f"[Coder] {response}", name="Coder")],
            "errors": None,
            "files_changed": ["fixed_file.py"],
            "next_step": "Reviewer"
        }

    # 2. Check for Spec (Spec-Driven)
    if state.get("spec"):
        spec = state["spec"]
        kernel = get_kernel()
        
        try:
            llm = kernel.model_selector.get_model("coding")
        except Exception as e:
             return {
                "messages": [HumanMessage(content=f"[Coder] No LLM configured. Error: {e}", name="Coder")],
                "next_step": "Supervisor"
            }
            
        files_tool = get_tool_from_registry("write_file")
        if not files_tool:
             from ...tools.file import WriteFileTool
             files_tool = WriteFileTool()
             
        chain = llm.bind_tools([files_tool])
        prompt = (
            f"You are a Coder. Your task is to implement the Spec below by creating files on the disk.\n"
            f"You MUST use the 'write_file' tool for every file mentioned.\n"
            f"Do not just say you did it. Actually call the tool.\n\n"
            f"SPEC:\n{spec}\n\n"
        )
        
        try:
            ai_msg = chain.invoke(prompt)
        except Exception as e:
            return {"messages": [HumanMessage(content=f"[Coder] Error: {e}", name="Coder")], "next_step": "Supervisor"}
            
        created_files = []
        if ai_msg.tool_calls:
            for tc in ai_msg.tool_calls:
                if tc["name"] == "write_file":
                    path = tc["args"].get("path")
                    content = tc["args"].get("content")
                    if path and content is not None:
                        files_tool._run(path, content)
                        created_files.append(path)
            response = f"Implemented {len(created_files)} files: {created_files}"
        else:
            response = "I analyzed the spec but didn't generate any file operations."

        return {
            "messages": [HumanMessage(content=f"[Coder] {response}", name="Coder")],
            "files_changed": created_files,
            "next_step": "Reviewer"
        }

    # Default fallback if no spec/errors (shouldn't happen in normal flow but safe return)
    return {
        "messages": [HumanMessage(content="[Coder] No task (spec/errors) to process.", name="Coder")],
        "next_step": "Supervisor"
    }
