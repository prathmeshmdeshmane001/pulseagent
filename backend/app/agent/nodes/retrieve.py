import time
from app.agent.state import AgentState
from app.tools.notion_mcp import search_notion

async def retrieve_notion_node(state: AgentState) -> dict:
    start_time = time.perf_counter()

    evidence_items = await search_notion(query=state.query)
    latency_ms = int((time.perf_counter() - start_time) * 1000)

    trace_entry = {
        "node_name": "retrieve_notion",
        "input_summary": f"Query: '{state.query}'",
        "output_summary": f"Retrieved {len(evidence_items)} Notion documents",
        "tokens_used": 0,
        "latency_ms": latency_ms
    }

    return {
        "evidence": state.evidence + evidence_items,
        "total_latency_ms": state.total_latency_ms + latency_ms,
        "trace_logs": state.trace_logs + [trace_entry]
    }
