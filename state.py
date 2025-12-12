from typing import List, Dict, Any
from pydantic import BaseModel, Field

class AgentState(BaseModel):
    # User input
    user_query: str = ""

    # Drafts
    draft: str = ""                    # current working draft
    previous_drafts: List[str] = []    # older drafts

    # Notes from agents
    safety_notes: List[str] = []
    critic_notes: List[str] = []

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=lambda: {
        "iterations": 0,
        "safety_pass": True,
        "critic_pass": True,
        "user_rejected": False,   # changed when user presses "Reject"
        "edited_by_user": False   # changed when user uses "Edit"
    })

    # UI final output (user approved)
    final_output: str = ""

    # Control flags (LangGraph uses these)
    user_action: str = ""   # "approve" / "edit" / "reject"
    edited_text: str = ""   # only for Edit mode

    class Config:
        arbitrary_types_allowed = True
