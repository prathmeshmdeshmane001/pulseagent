import os
import logging
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState

# Nodes
from app.agent.nodes.input_guardrail import input_guardrail_node
from app.agent.nodes.decompose import decompose_node
from app.agent.nodes.retrieve_multi import retrieve_multi_node
from app.agent.nodes.memory_nodes import memory_read_node, memory_write_node
from app.agent.nodes.synthesize import synthesize_node
from app.agent.nodes.pii_redact import pii_redact_node
from app.agent.nodes.citation_validate import citation_validate_node
from app.agent.nodes.output_validate import output_validate_node
from app.agent.nodes.permission_gate import permission_gate_node

logger = logging.getLogger("pulseagent.graph")

# Observability check for LangSmith
if os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1") and not os.getenv("LANGCHAIN_API_KEY"):
    logger.warning("LANGCHAIN_TRACING_V2 is enabled but LANGCHAIN_API_KEY is missing. Tracing will proceed locally.")

def check_guardrail_condition(state: AgentState) -> str:
    if state.guardrail_blocked:
        return "blocked"
    return "continue"

def check_permission_condition(state: AgentState) -> str:
    if state.pending_action:
        return "gated"
    return "continue"

def build_full_agent_graph():
    builder = StateGraph(AgentState)

    # Add all 10 nodes according to architecture diagram
    builder.add_node("input_guardrail", input_guardrail_node)
    builder.add_node("decompose", decompose_node)
    builder.add_node("retrieve_multi", retrieve_multi_node)
    builder.add_node("memory_read", memory_read_node)
    builder.add_node("synthesize", synthesize_node)
    builder.add_node("pii_redact", pii_redact_node)
    builder.add_node("citation_validate", citation_validate_node)
    builder.add_node("output_validate", output_validate_node)
    builder.add_node("permission_gate", permission_gate_node)
    builder.add_node("memory_write", memory_write_node)

    # Entry point: input guardrail
    builder.set_entry_point("input_guardrail")

    # Conditional routing after input guardrail
    builder.add_conditional_edges(
        "input_guardrail",
        check_guardrail_condition,
        {
            "blocked": END,
            "continue": "decompose"
        }
    )

    # Multi-hop retrieval and memory read pipeline
    builder.add_edge("decompose", "retrieve_multi")
    builder.add_edge("retrieve_multi", "memory_read")
    builder.add_edge("memory_read", "synthesize")
    builder.add_edge("synthesize", "pii_redact")
    builder.add_edge("pii_redact", "citation_validate")
    builder.add_edge("citation_validate", "output_validate")
    builder.add_edge("output_validate", "permission_gate")

    # Conditional routing after permission gate
    builder.add_conditional_edges(
        "permission_gate",
        check_permission_condition,
        {
            "gated": END,
            "continue": "memory_write"
        }
    )

    builder.add_edge("memory_write", END)

    return builder.compile()

agent_graph = build_full_agent_graph()

async def run_agent(query: str, session_id: str = "default_session", user_id: str = "default_user") -> AgentState:
    initial_state = AgentState(
        query=query,
        session_id=session_id,
        user_id=user_id
    )
    result = await agent_graph.ainvoke(initial_state)
    if isinstance(result, dict):
        return AgentState(**result)
    return result
