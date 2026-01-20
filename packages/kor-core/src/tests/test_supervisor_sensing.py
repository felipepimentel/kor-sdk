
import pytest
from langchain_core.prompts import ChatPromptTemplate
from kor_core.agent.nodes.supervisor import system_prompt_template

def test_supervisor_prompt_includes_plan():
    # Setup the prompt exactly as in supervisor.py
    # We strip the "PromptLoader.load" part because in test env it usually falls back to the string default
    # The variable 'system_prompt_template' in the module IS the string (or loaded string).
    
    assert "{plan}" in system_prompt_template, "System prompt must contain {plan} placeholder"
    
    prompt = ChatPromptTemplate.from_template(system_prompt_template)
    
    # Simulate data
    plan_str = "[x] Task 1\n[/] Task 2"
    members = "Coder, Architect"
    
    # Format
    messages = prompt.format_messages(plan=plan_str, members=members)
    content = messages[0].content
    
    # Verify sensing
    assert "CURRENT PLAN:" in content
    assert "[x] Task 1" in content
    assert "[/] Task 2" in content
    assert "Coder, Architect" in content
