from typing import Dict, Any, Literal
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
# Removed: from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .state import AgentState
from ..config import ConfigManager
from ..prompts import PromptLoader
from ..kernel import get_kernel
from langchain_core.output_parsers import StrOutputParser
from ..tools.terminal import TerminalTool
from ..tools.browser import BrowserTool

def get_tool_from_registry(name: str):
    """Attempt to get a tool from the global registry, fallback to defaults."""
    try:
        from ..kernel import get_kernel
        k = get_kernel()
        k.boot()
        registry = k.registry.get_service("tools")
        if registry:
            tool_info = registry.get(name)
            if tool_info:
                tool = tool_info.tool_class()
                # Inject registry if the tool needs it (e.g. SearchToolsTool)
                if hasattr(tool, "registry"): tool.registry = registry
                return tool
                
            # If name is not found, try a semantic search as fallback?
            # For now, we prefer exact names or known fallbacks.
    except Exception as e:
        print(f"Tool lookup error: {e}")
        pass
    
    # Fallbacks for built-in tools if registry is missing
    if name == "terminal": return TerminalTool()
    if name == "browser": return BrowserTool()
    return None

def get_best_tool_for_node(node_name: str, task_context: str = "") -> Any:
    """Discovers the best tool for a given node based on defaults or registry."""
    # Mapping of nodes to their 'preferred' primary tool
    defaults = {
        "Coder": "terminal",
        "Researcher": "browser",
        "Explorer": "search_tools",
        "Architect": "search_symbols",
        "Reviewer": "terminal"
    }
    
    # 1. Check if the task context explicitly mentions a tool
    # 2. Return the default for the node
    tool_name = defaults.get(node_name)
    return get_tool_from_registry(tool_name) if tool_name else None


# --- Supervisor Node ---
from ..prompts import PromptLoader

# --- Supervisor Node ---
from ..prompts import PromptLoader

# Load prompt from file
system_prompt_template = PromptLoader.load("supervisor")
# Fallback if file load fails
if not system_prompt_template:
    system_prompt_template = (
        "You are a supervisor tasked with managing a conversation between the"
        " following workers: {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )

def supervisor_node(state: AgentState):
    """Decides which worker should act next."""
    # Get dynamic members from config
    from ..kernel import get_kernel
    kernel = get_kernel()
    
    # We use the configured members OR fall back to standard ones if config is empty
    members = kernel.config.agent.supervisor_members or ["Architect", "Coder", "Reviewer", "Researcher", "Explorer"]
    options = ["FINISH"] + members
    
    # Use "supervisor" purpose for routing (fast mode recommended)
    try:
        llm = kernel.model_selector.get_model("supervisor")
    except Exception:
        llm = None
    
    if not llm:
        # Fallback logic for basic tests if no LLM configured
        last_msg_obj = state['messages'][-1]
        
        # Check if last message is from one of the members
        if hasattr(last_msg_obj, "name") and last_msg_obj.name in members:
             return {"next_step": "FINISH"}

        last_msg = last_msg_obj.content.lower()
        if "create" in last_msg or "design" in last_msg:
             return {"next_step": "Architect"} if "Architect" in members else {"next_step": "Coder"}

        if "code" in last_msg or "file" in last_msg:
             return {"next_step": "Coder"} if "Coder" in members else {"next_step": "FINISH"}
        
        return {"next_step": "FINISH"}

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt_template),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), members=", ".join(members))

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

# --- Worker Nodes ---

def coder_node(state: AgentState):
    """
    Coder Worker. Translates Spec to Code.
    """
    last_msg = state['messages'][-1].content
    
    # 1. Check for Errors (Self-Healing)
    if state.get("errors"):
        errors = state["errors"]
        response = f"Fixing errors: {errors}"
        # In real world: Run terminal to fix specific file
        return {
            "messages": [HumanMessage(content=f"[Coder] {response}", name="Coder")],
            "errors": None, # Clear errors after fixing
            "files_changed": ["fixed_file.py"], # Mock update
            "next_step": "Reviewer" # Send back to review
        }

    # 2. Check for Spec (Spec-Driven)
    if state.get("spec"):
        spec = state["spec"]
        kernel = get_kernel()
        
        # Get Coder LLM
        try:
            llm = kernel.model_selector.get_model("coding")
        except Exception as e:
             return {
                "messages": [HumanMessage(content=f"[Coder] No LLM configured. Error: {e}", name="Coder")],
                "next_step": "Supervisor"
            }
            
        # Bind WriteFileTool
        files_tool = get_tool_from_registry("write_file")
        if not files_tool:
             # Fallback if registry fails?
             from ..tools.file import WriteFileTool
             files_tool = WriteFileTool()
             
        # Create a simple chain: System -> User (Spec) -> LLM (with Tools)
        # We need the LLM to actually call the tool.
        chain = llm.bind_tools([files_tool])
        
        prompt = (
            f"You are a Coder. Your task is to implement the Spec below by creating files on the disk.\n"
            f"You MUST use the 'write_file' tool for every file mentioned.\n"
            f"Do not just say you did it. Actually call the tool.\n\n"
            f"SPEC:\n{spec}\n\n"
        )
        
        try:
            print(f"[Debug] Coder Invoking LLM with Prompt len: {len(prompt)}")
            ai_msg = chain.invoke(prompt)
            print(f"[Debug] Coder Response: {ai_msg.content}")
            print(f"[Debug] Tool Calls: {ai_msg.tool_calls}")
        except Exception as e:
            return {"messages": [HumanMessage(content=f"[Coder] Error: {e}", name="Coder")], "next_step": "Supervisor"}
            
        # Execute Tool Calls
        created_files = []
        if ai_msg.tool_calls:
            for tc in ai_msg.tool_calls:
                if tc["name"] == "write_file":
                    # Execute
                    path = tc["args"].get("path")
                    content = tc["args"].get("content")
                    if path and content is not None:
                        files_tool._run(path, content)
                        created_files.append(path)
                        
            response = f"Implemented {len(created_files)} files: {created_files}"
        else:
            response = "I analyzed the spec but didn't generate any file operations. (Did you forget to provide a complete spec?)"

        return {
            "messages": [HumanMessage(content=f"[Coder] {response}", name="Coder")],
            "files_changed": created_files,
            "next_step": "Reviewer"
        }

    # 3. Fallback / Legacy Mode
    tool = get_best_tool_for_node("Coder", last_msg)
    response = "I am ready to code."
    
    if "list" in last_msg.lower():
        output = tool._run("ls -la") if tool else "No tool available"
        response = f"Listing files:\n{output}"
    
    return {
        "messages": [
            HumanMessage(content=f"[Coder] {response}", name="Coder")
        ],
        "next_step": "Supervisor" # Default legacy behavior
    }

def researcher_node(state: AgentState):
    """
    Researcher Worker. Can search the web.
    """
    last_msg = state['messages'][-1].content
    tool = get_best_tool_for_node("Researcher", last_msg)
    
    response = "I am ready to research."
    # Naive extraction (in real world an Agent would decide arguments)
    if "search" in last_msg.lower() or "research" in last_msg.lower():
        # Strip "search"
        query = last_msg.replace("search", "").replace("research", "").strip() or "python mcp"
        output = tool._run(query) if tool else "No tool available"
        response = f"Search Results for '{query}':\n{output}"

    return {
        "messages": [
            HumanMessage(content=f"[Researcher] {response}", name="Researcher")
        ]
    }

def explorer_node(state: AgentState):
    """
    Discovery Worker. Can search for available tools.
    """
    last_msg = state['messages'][-1].content
    tool = get_best_tool_for_node("Explorer", last_msg)
    
    response = "I am ready to discover capabilities."
    if "tool" in last_msg.lower() or "find" in last_msg.lower():
        query = last_msg.replace("find", "").replace("tool", "").strip() or "general"
        output = tool._run(query) if tool else "No tool available"
        response = f"Discovered Capabilities for '{query}':\n{output}"
        
    return {
        "messages": [
            HumanMessage(content=f"[Explorer] {response}", name="Explorer")
        ]
    }

def architect_node(state: AgentState):
    """
    Architect. Creates technical specs.
    """
    last_msg = state['messages'][-1].content
    kernel = get_kernel()
    
    # Load Prompt
    system_prompt = PromptLoader.load("architect") or "You are an Architect. Create a spec for the user request."
    
    try:
        # Use coding model or architect model
        llm = kernel.model_selector.get_model("coding") 
    except:
        # Fallback to mock if no model configured (e.g. tests)
        spec = f"SPECIFICATION (Mock) for: {last_msg}\n1. Create component.\n2. Add props."
        return {
            "messages": [HumanMessage(content=f"[Architect] {spec}", name="Architect")],
            "spec": spec,
            "next_step": "Coder"
        }

    # Context Injection (Type-Aware RAG - Lite) with LSP Senses
    # Architect uses search_symbols and LSP tools to "Sense" the codebase
    
    # For now, we manually suggest using tools in the prompt if available
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

async def reviewer_node(state: AgentState):
    """
    Reviewer. Validates code.
    """
    files = state.get("files_changed", [])
    spec = state.get("spec", "")
    
    if not files:
        return {"messages": [HumanMessage(content="[Reviewer] No files to review.", name="Reviewer")], "next_step": "Supervisor"}
        
    kernel = get_kernel()
    system_prompt = PromptLoader.load("reviewer") or "You are a Reviewer. Check the code."
    
    try:
        llm = kernel.model_selector.get_model("coding")
    except:
        # Mock Pass
        return {
            "messages": [HumanMessage(content=f"[Reviewer] PASS (Mock)", name="Reviewer")],
            "next_step": "Supervisor"
        }
    
    # 1. Shadow Validation (LSP/Linter)
    from ..validation.registry import LanguageRegistry
    registry = LanguageRegistry(kernel.config.languages)
    
    # Batch validation (Refactored)
    validation_feedback = await registry.validate_files(files)
    has_validation_errors = len(validation_feedback) > 0
    
    validation_msg = ""
    if has_validation_errors:
        validation_msg = "\n\nAUTOMATED VALIDATION FAILED:\n" + "\n".join(validation_feedback)
             
    chain = (
        ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Spec: {spec}\n\nFiles Changed:\n{files}\n{validation}")
        ])
        | llm
        | StrOutputParser()
    )
    
    from pathlib import Path
    file_contents = ""
    for f in files:
         path = Path(f)
         if path.exists():
             file_contents += f"--- {f} ---\n{path.read_text()}\n"
    
    try:
        # We assume strict compliance: if validation fails, LLM should see it and likely FAIL.
        review_result = await chain.ainvoke({"spec": spec, "files": file_contents, "validation": validation_msg})
    except Exception as e:
        review_result = f"Error reviewing: {e}"
        
    # Analyze result for PASS/FAIL
    if "PASS" in review_result and not has_validation_errors:
        next_step = "Supervisor"
        errors = None
    else:
        next_step = "Coder" # Loop back
        # If LLM said PASS but we have validation errors, we force fail?
        # Ideally LLM sees the validation errors and says FAIL. 
        # But if it hallucinates PASS, we should override or append validation errors.
        if has_validation_errors and "PASS" in review_result:
             review_result = f"AUTO-FAIL: Validation errors detected despite LLM approval.\n{validation_msg}"
        
        errors = [review_result] # Treat the whole message as feedback
    
    return {
        "messages": [HumanMessage(content=f"[Reviewer] {review_result}", name="Reviewer")],
        "errors": errors,
        "next_step": next_step
    }
