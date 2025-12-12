from agent.prompts import SAFETY_PROMPT
from agent.llm_client import generate_response

def safety_agent(state):
    prompt = SAFETY_PROMPT.format(draft=state.draft)
    result = generate_response(prompt)

    updates = {
        "metadata": {**state.metadata, "safety_pass": result.strip() == "SAFE"}
    }
    
    if result.strip() != "SAFE":
        updates["safety_notes"] = state.safety_notes + [result]

    return updates

