"""
Auto Planner Node for KOR Agents.

This node generates a plan automatically using an LLM when:
1. No PLAN.md exists in the workspace
2. A user_goal is present in the state

This enables fully autonomous "Plan-and-Execute" behavior.
"""
from pathlib import Path
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from ..state import AgentState
from ..planning import Planner
from ...kernel import get_kernel
import logging

logger = logging.getLogger(__name__)

PLAN_GENERATION_PROMPT = """You are a task planner. Given the user's goal, break it down into clear, actionable tasks.

USER GOAL:
{user_goal}

Output a numbered list of tasks. Each task should be:
- Specific and actionable
- Independent when possible
- Ordered logically

Format (one task per line):
1. First task description
2. Second task description
...

Only output the numbered list, nothing else."""


def auto_planner_node(state: AgentState) -> Dict[str, Any]:
    """
    Node that auto-generates a plan from user_goal if no plan exists.
    
    Behavior:
    - If PLAN.md exists: Do nothing (EnsurePlan handles it).
    - If no PLAN.md but user_goal exists: Generate plan via LLM.
    - If no user_goal: Do nothing.
    """
    kernel = get_kernel()
    plan_path = Path("PLAN.md")
    
    # Skip if plan already exists
    if plan_path.exists():
        logger.debug("AutoPlanner: PLAN.md exists, skipping generation.")
        return {}
    
    # Skip if there's already a plan in state
    if state.get("plan") and len(state["plan"]) > 0:
        logger.debug("AutoPlanner: Plan already in state, skipping generation.")
        return {}
    
    # Get user goal from state or first message
    user_goal = state.get("user_goal")
    if not user_goal and state.get("messages"):
        # Extract goal from first human message
        first_msg = state["messages"][0]
        if hasattr(first_msg, "content"):
            user_goal = first_msg.content
    
    if not user_goal:
        logger.debug("AutoPlanner: No user_goal found, skipping generation.")
        return {}
    
    # Get LLM for planning
    try:
        llm = kernel.model_selector.get_model("planner")
    except Exception:
        try:
            llm = kernel.model_selector.get_model("default")
        except Exception:
            logger.warning("AutoPlanner: No LLM available for plan generation.")
            return {}
    
    if not llm:
        return {}
    
    # Generate plan
    logger.info(f"AutoPlanner: Generating plan for goal: {user_goal[:100]}...")
    
    prompt = ChatPromptTemplate.from_template(PLAN_GENERATION_PROMPT)
    chain = prompt | llm
    
    try:
        response = chain.invoke({"user_goal": user_goal})
        plan_text = response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        logger.error(f"AutoPlanner: LLM call failed: {e}")
        return {}
    
    # Parse response into tasks
    planner = Planner()
    lines = plan_text.strip().split("\n")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Remove numbering (e.g., "1. ", "2) ")
        import re
        cleaned = re.sub(r'^[\d]+[\.\)]\s*', '', line)
        if cleaned:
            planner.add_task(cleaned)
    
    if planner.tasks:
        # Write to file
        planner.bind_to_file(plan_path)
        planner._write_to_file()
        
        # Mark first task as active
        if planner.tasks:
            planner.update_task_status(planner.tasks[0]["id"], "active")
        
        logger.info(f"AutoPlanner: Generated plan with {len(planner.tasks)} tasks.")
        
        return {
            "plan": planner.tasks,
            "current_task_id": planner.current_task_id
        }
    
    return {}
