from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    The state of the KOR agent graph.
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next_step: str
