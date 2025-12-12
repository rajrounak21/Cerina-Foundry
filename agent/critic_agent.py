from agent.prompts import CRITIC_PROMPT
from agent.llm_client import generate_response

def critic_agent(state):
    prompt = CRITIC_PROMPT.format(draft=state.draft)
    result = generate_response(prompt)

    updates = {
        "metadata": {**state.metadata, "critic_pass": result.strip() == "GOOD"}
    }
    
    if result.strip() != "GOOD":
        updates["critic_notes"] = state.critic_notes + [result]

    return updates

