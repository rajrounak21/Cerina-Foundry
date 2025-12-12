import sys
import os
import uuid

# Add project root to path so we can import modules from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp.server.fastmcp import FastMCP
from graph_builder import build_graph
from checkpoint_store import get_checkpointer_context

# Initialize MCP Server
mcp = FastMCP("cerina_foundry")

@mcp.tool()
def generate_cbt_exercise(topic: str, instructions: str = "") -> str:
    """
    Generates a CBT (Cognitive Behavioral Therapy) exercise or protocol based on the topic and instructions.
    Use this tool when the user asks to create an exercise, protocol, or therapeutic content.
    The process involves an AI agent drafting, safety checking, and clinical critiquing the content.
    
    Args:
        topic: The main topic (e.g., "Sleep Hygiene", "Social Anxiety Exposure").
        instructions: Additional details or specific requirements.
    
    Returns:
        The generated therapeutic content or a report on why it couldn't be completed.
    """
    
    # Combine input into a query
    user_query = f"{topic}. {instructions}".strip()
    thread_id = f"mcp-{uuid.uuid4().hex[:8]}"
    
    # Initial State matching AgentState definition
    initial_state = {
        "user_query": user_query,
        "draft": "",
        "previous_drafts": [],
        "safety_notes": [],
        "critic_notes": [],
        "metadata": {
            "iterations": 0, 
            "safety_pass": True, 
            "critic_pass": True,
            "user_rejected": False, 
            "edited_by_user": False
        },
        "final_output": "", 
        "user_action": "", 
        "edited_text": ""
    }
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Use existing checkpoint system to ensure we use the same DB logic
        with get_checkpointer_context() as checkpointer:
            graph = build_graph(checkpointer)
            
            # Invoke the graph synchronously
            # This runs the full autonomous loop until it hits "human_approval" or "human_approval_done"
            # Since MCP is machine-to-machine, we might want to auto-approve or return the draft for review.
            # For now, let's assume we want to reach the "human_approval" state and return that result.
            
            result = graph.invoke(initial_state, config=config)
            
            # Extract results
            # Result is a dict of the final state
            final_output = result.get("final_output")
            draft = result.get("draft")
            
            # Since the graph stops at 'human_approval' (waiting for user), 'final_output' might be empty unless we auto-approve.
            # But the user request implies getting a result.
            # If the graph pauses at human_approval, we should probably output the draft.
            
            if final_output:
                return f"FINAL APPROVED CONTENT:\n\n{final_output}"
            
            # Check if we are waiting for approval
            next_node = result.get("metadata", {}).get("next_node")
            if next_node == "human_approval":
                return f"GENERATED DRAFT (Requires Approval):\n\n{draft}\n\n[System Note: This content passed Safety and Critic checks but requires human approval. In an MCP context, you can consider this the proposed response.]"
            
            # If it failed or looped out
            safety_notes = "\n".join(result.get("safety_notes", []))
            critic_notes = "\n".join(result.get("critic_notes", []))
            return f"INCOMPLETE/BLOCKED:\n\nDraft:\n{draft}\n\nSafety Notes:\n{safety_notes}\n\nCritic Notes:\n{critic_notes}"

    except Exception as e:
        return f"Error executing Cerina workflow: {str(e)}"

def main():
    # Initialize and run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()
