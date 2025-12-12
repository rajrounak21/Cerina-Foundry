def supervisor_agent(state):
    user_action = state.user_action

    # ------------------------------------
    # 1) USER CHOSE APPROVE
    # ------------------------------------
    if user_action == "approve":
        return {
            "final_output": state.draft,
            "metadata": {**state.metadata, "next_node": "human_approval_done"},
            "user_action": ""
        }
        

    # ------------------------------------
    
    # 2) USER CHOSE EDIT
    # ------------------------------------
    if user_action == "edit":
        return {
            "draft": state.edited_text,
            "metadata": {**state.metadata, "edited_by_user": True, "next_node": "safety"},
            "user_action": ""
        }


    # ------------------------------------
    # 3) USER CHOSE REJECT
    # ------------------------------------
    if user_action == "reject":
        return {
            "metadata": {**state.metadata, "user_rejected": True, "next_node": "drafter"},
            "previous_drafts": state.previous_drafts + [state.draft],
            "draft": "",
            "user_action": ""
        }


    # ------------------------------------
    # INTERNAL FLOW — no user action yet
    # ------------------------------------
    
    # If no draft exists yet → create one
    if not state.draft or state.draft.strip() == "":
        return {"metadata": {**state.metadata, "next_node": "drafter"}}

    # If safety failed → rewrite
    if not state.metadata.get("safety_pass", True):
        return {"metadata": {**state.metadata, "next_node": "drafter"}}

    # If critic failed → rewrite
    if not state.metadata.get("critic_pass", True):
        return {"metadata": {**state.metadata, "next_node": "drafter"}}

    # Everything good → ask human approval
    return {"metadata": {**state.metadata, "next_node": "human_approval"}}

