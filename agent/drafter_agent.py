from agent.prompts import DRAFTER_PROMPT, DRAFTER_PROMPT_WITH_CONTEXT
from agent.llm_client import generate_response

def drafter_agent(state):
    """
    Drafter agent that learns from rejected drafts and feedback.
    If there are previous rejected drafts, it uses context to avoid repeating mistakes.
    """
    
    # Check if we have context from previous attempts
    has_rejected_drafts = state.metadata.get("user_rejected", False)
    has_previous_drafts = len(state.previous_drafts) > 0
    has_feedback = len(state.safety_notes) > 0 or len(state.critic_notes) > 0
    
    # Build context if we have previous attempts
    if has_rejected_drafts or (has_previous_drafts and has_feedback):
        context_parts = []
        
        # Add information about rejected drafts
        if has_rejected_drafts and has_previous_drafts:
            num_rejected = len(state.previous_drafts)
            context_parts.append(f"The user has REJECTED {num_rejected} previous draft(s).")
            context_parts.append("They want a DIFFERENT approach, not just minor edits.")
            
            # Show the most recent rejected draft as reference
            if state.previous_drafts:
                last_rejected = state.previous_drafts[-1]
                context_parts.append(f"\nMost recently rejected draft:\n---\n{last_rejected[:500]}...\n---")
        
        # Add feedback from safety/critic agents
        if state.safety_notes:
            context_parts.append("\nPrevious Safety Concerns:")
            for note in state.safety_notes[-3:]:  # Last 3 safety notes
                context_parts.append(f"  - {note}")
        
        if state.critic_notes:
            context_parts.append("\nPrevious Quality Feedback:")
            for note in state.critic_notes[-3:]:  # Last 3 critic notes
                context_parts.append(f"  - {note}")
        
        # Use context-aware prompt
        context = "\n".join(context_parts)
        prompt = DRAFTER_PROMPT_WITH_CONTEXT.format(
            user_query=state.user_query,
            context=context
        )
    else:
        # First attempt - use standard prompt
        prompt = DRAFTER_PROMPT.format(user_query=state.user_query)
    
    # Generate the draft
    new_draft = generate_response(prompt, stream_output=True)

    # Build the updates dictionary
    updates = {
        "draft": new_draft,
        "metadata": {
            **state.metadata, 
            "iterations": state.metadata.get("iterations", 0) + 1,
            "user_rejected": False  # Reset rejection flag after processing
        }
    }
    
    # Add old draft to previous drafts if it exists
    if state.draft:
        updates["previous_drafts"] = state.previous_drafts + [state.draft]
    
    return updates

