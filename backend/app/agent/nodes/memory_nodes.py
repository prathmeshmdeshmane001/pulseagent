import time
from app.agent.state import AgentState
from app.db.session import AsyncSessionLocal
from app.memory.long_term import retrieve_long_term_memories
from app.memory.memory_manager import extract_and_store_facts

async def memory_read_node(state: AgentState) -> dict:
    start_time = time.perf_counter()

    async with AsyncSessionLocal() as db:
        memories = await retrieve_long_term_memories(
            query=state.query,
            user_id=state.user_id,
            db=db,
            top_k=3
        )

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    trace_entry = {
        "node_name": "memory_read",
        "input_summary": f"Query: '{state.query}'",
        "output_summary": f"Recalled {len(memories)} facts: " + "; ".join(memories) if memories else "No relevant long-term facts found",
        "tokens_used": 0,
        "latency_ms": latency_ms
    }

    return {
        "memories": memories,
        "total_latency_ms": state.total_latency_ms + latency_ms,
        "trace_logs": state.trace_logs + [trace_entry]
    }

async def memory_write_node(state: AgentState) -> dict:
    start_time = time.perf_counter()

    stored_facts = []
    # Only write memory if not blocked by guardrails and there is a valid answer
    if not state.guardrail_blocked and state.final_answer:
        async with AsyncSessionLocal() as db:
            stored_facts = await extract_and_store_facts(
                query=state.query,
                final_answer=state.final_answer,
                session_id=state.session_id,
                user_id=state.user_id,
                db=db
            )

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    trace_entry = {
        "node_name": "memory_write",
        "input_summary": f"Answer length: {len(state.final_answer)} chars",
        "output_summary": f"Promoted {len(stored_facts)} durable facts to long-term memory" if stored_facts else "No durable facts promoted",
        "tokens_used": 50 if stored_facts else 0,
        "latency_ms": latency_ms
    }

    return {
        "total_latency_ms": state.total_latency_ms + latency_ms,
        "trace_logs": state.trace_logs + [trace_entry]
    }
