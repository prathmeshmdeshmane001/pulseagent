import time
import asyncio
from typing import List
from app.agent.state import AgentState
from app.models.evidence import Evidence
from app.tools.notion_mcp import search_notion
from app.tools.gmail_mcp import search_gmail
from app.tools.jira_mcp import search_jira

async def dispatch_tool_call(source: str, query: str, sub_question_id: str) -> List[Evidence]:
    try:
        if source == "notion":
            return await search_notion(query, sub_question_id=sub_question_id)
        elif source == "gmail":
            return await search_gmail(query, sub_question_id=sub_question_id)
        elif source == "jira":
            return await search_jira(query, sub_question_id=sub_question_id)
    except Exception as e:
        # Graceful degradation on tool failures
        return []
    return []

async def retrieve_multi_node(state: AgentState) -> dict:
    start_time = time.perf_counter()

    tasks = []
    # If no sub_questions, query all 3 for the main query
    if not state.sub_questions:
        tasks.append(dispatch_tool_call("notion", state.query, "sq_root"))
        tasks.append(dispatch_tool_call("gmail", state.query, "sq_root"))
        tasks.append(dispatch_tool_call("jira", state.query, "sq_root"))
    else:
        for sq in state.sub_questions:
            for src in sq.sources:
                tasks.append(dispatch_tool_call(src, sq.text, sq.id))

    # Run tool dispatches in parallel
    results_lists = await asyncio.gather(*tasks, return_exceptions=False)

    aggregated_evidence: List[Evidence] = []
    seen_snippets = set()

    for ev_list in results_lists:
        for ev in ev_list:
            key = (ev.source, ev.permalink, ev.snippet[:50])
            if key not in seen_snippets:
                seen_snippets.add(key)
                aggregated_evidence.append(ev)

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    by_source = {}
    for ev in aggregated_evidence:
        by_source[ev.source] = by_source.get(ev.source, 0) + 1

    summary_counts = ", ".join(f"{k}: {v}" for k, v in by_source.items())

    trace_entry = {
        "node_name": "retrieve_multi",
        "input_summary": f"Dispatched {len(tasks)} parallel queries across sources",
        "output_summary": f"Retrieved {len(aggregated_evidence)} total evidence items ({summary_counts})",
        "tokens_used": 0,
        "latency_ms": latency_ms
    }

    return {
        "evidence": aggregated_evidence,
        "total_latency_ms": state.total_latency_ms + latency_ms,
        "trace_logs": state.trace_logs + [trace_entry]
    }
