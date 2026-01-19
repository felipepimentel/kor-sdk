from pathlib import Path
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...prompts import PromptLoader
from ...kernel import get_kernel
from ..state import AgentState

async def reviewer_node(state: AgentState):
    """Reviewer. Validates code."""
    files = state.get("files_changed", [])
    spec = state.get("spec", "")
    
    if not files:
        return {"messages": [HumanMessage(content="[Reviewer] No files to review.", name="Reviewer")], "next_step": "Supervisor"}
        
    kernel = get_kernel()
    system_prompt = PromptLoader.load("reviewer") or "You are a Reviewer. Check the code."
    
    try:
        llm = kernel.model_selector.get_model("coding")
    except Exception:
        return {
            "messages": [HumanMessage(content="[Reviewer] PASS (Mock)", name="Reviewer")],
            "next_step": "Supervisor"
        }
    
    from ...validation.registry import LanguageRegistry
    registry = LanguageRegistry(kernel.config.languages)
    
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
    
    file_contents = ""
    for f in files:
         path = Path(f)
         if path.exists():
             file_contents += f"--- {f} ---\n{path.read_text()}\n"
    
    try:
        review_result = await chain.ainvoke({"spec": spec, "files": file_contents, "validation": validation_msg})
    except Exception as e:
        review_result = f"Error reviewing: {e}"
        
    if "PASS" in review_result and not has_validation_errors:
        next_step = "Supervisor"
        errors = None
    else:
        next_step = "Coder"
        if has_validation_errors and "PASS" in review_result:
             review_result = f"AUTO-FAIL: Validation errors detected despite LLM approval.\n{validation_msg}"
        errors = [review_result]
    
    return {
        "messages": [HumanMessage(content=f"[Reviewer] {review_result}", name="Reviewer")],
        "errors": errors,
        "next_step": next_step
    }
