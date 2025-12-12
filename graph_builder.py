import os
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

from finalizer import finalizer_node
from state import AgentState
from agent.drafter_agent import drafter_agent
from agent.safety_agent import safety_agent
from agent.critic_agent import critic_agent
from agent.supervisor_agent import supervisor_agent
from langsmith import traceable  # ✅ replaces LangChainTracer

# Optional: Suppress blocking warnings for local run
os.environ["BG_JOB_ISOLATED_LOOPS"] = "true"

#  LangSmith tracing setup
os.environ["LANGSMITH_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "pr-rundown-ant-95")




def build_graph(checkpointer=None):
    graph = StateGraph(AgentState)

    # Use Neon checkpointer if provided; else use memory
    if checkpointer is None:
        checkpointer = MemorySaver()

    # ----------------------
    # Nodes
    # ----------------------
    graph.add_node("drafter", drafter_agent)
    graph.add_node("safety", safety_agent)
    graph.add_node("critic", critic_agent)
    graph.add_node("supervisor", supervisor_router)

    graph.add_node("human_approval", lambda state: state)
    graph.add_node("human_approval_done", finalizer_node)

    # ----------------------
    # Entry point
    # ----------------------
    graph.set_entry_point("supervisor")

    # ----------------------
    # Edges
    # ----------------------
    graph.add_edge("drafter", "safety")
    graph.add_edge("safety", "critic")
    graph.add_edge("critic", "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        supervisor_condition,
        {
            "drafter": "drafter",
            "safety": "safety",  # needed ONLY for edit cases
            "human_approval": "human_approval",
            "human_approval_done": "human_approval_done",
        },
    )

    return graph.compile(checkpointer=checkpointer)


# ------------------------------
# Helper wrappers
# ------------------------------

def supervisor_router(state: AgentState):
    """
    Wrapper: supervisor_agent updates state + next_node.
    """
    # Run supervisor agent (returns state)
    updated_state = supervisor_agent(state)

    # Ensure next_node is present
    if "next_node" not in updated_state["metadata"]:
        updated_state["metadata"]["next_node"] = "human_approval"

    return updated_state


def supervisor_condition(state: AgentState):
    """
    Graph routing based on supervisor next_node.
    """
    return state.metadata["next_node"]
