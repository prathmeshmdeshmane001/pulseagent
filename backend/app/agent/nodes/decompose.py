import time
import json
from typing import List
from pydantic import BaseModel, Field
from app.agent.state import AgentState, SubQuestion
from app.agent.llm_client import llm_client

# UNTRUSTED DATA BOUNDARY:
# Decomposer strictly operates on user queries and conversation state. Any external retrieved text
# or documents must never be evaluated as prompt directives or override system instructions.

class DecomposeResponse(BaseModel):
    sub_questions: List[SubQuestion]

async def decompose_node(state: AgentState) -> dict:
    start_time = time.perf_counter()

    prompt = (
        f"You are the query decomposition node of PulseAgent.\n"
        f"Decompose the following user question into 2 to 4 targeted, non-redundant sub-questions.\n"
        f"For each sub-question, specify which data sources should be queried: notion, gmail, or jira.\n"
        f"- Use 'notion' for architecture docs, specs, notes, roadmaps, goals, guidelines.\n"
        f"- Use 'jira' for sprint tasks, tickets, issue keys, assignees, bug status, blockers.\n"
        f"- Use 'gmail' for emails, recent correspondence, stakeholder discussions, meeting notes.\n\n"
        f"User Question: {state.query}\n\n"
        f"Return strict JSON format matching this schema:\n"
        f"{{\n"
        f'  "sub_questions": [\n'
        f'    {{"id": "sq1", "text": "...", "sources": ["notion"]}},\n'
        f'    {{"id": "sq2", "text": "...", "sources": ["jira"]}}\n'
        f"  ]\n"
        f"}}"
    )

    result = await llm_client.generate_gemini(prompt=prompt, json_mode=True, temperature=0.1)
    latency_ms = int((time.perf_counter() - start_time) * 1000)

    sub_questions: List[SubQuestion] = []
    try:
        data = json.loads(result.text)
        raw_items = data.get("sub_questions", [])
        for idx, item in enumerate(raw_items):
            sq_id = item.get("id") or f"sq_{idx+1}"
            sq_text = item.get("text", "")
            sq_sources = item.get("sources", ["notion", "gmail", "jira"])
            valid_sources = [s.lower() for s in sq_sources if s.lower() in ("notion", "gmail", "jira")]
            if not valid_sources:
                valid_sources = ["notion"]
            if sq_text:
                sub_questions.append(SubQuestion(id=sq_id, text=sq_text, sources=valid_sources))
    except Exception:
        # Fallback subquestions based on standard decomposition
        sub_questions = [
            SubQuestion(id="sq_1", text=f"What are the specifications and documentation regarding: {state.query}?", sources=["notion"]),
            SubQuestion(id="sq_2", text=f"What are the sprint tasks and tickets for: {state.query}?", sources=["jira"]),
            SubQuestion(id="sq_3", text=f"What are the latest emails and messages regarding: {state.query}?", sources=["gmail"])
        ]

    if not sub_questions:
        sub_questions = [
            SubQuestion(id="sq_1", text=state.query, sources=["notion", "jira", "gmail"])
        ]

    trace_entry = {
        "node_name": "decompose",
        "input_summary": f"Query: '{state.query}'",
        "output_summary": f"Generated {len(sub_questions)} sub-questions: " + ", ".join(f"[{sq.id}: {sq.text[:40]}... -> {sq.sources}]" for sq in sub_questions),
        "tokens_used": result.tokens_used,
        "latency_ms": latency_ms
    }

    return {
        "sub_questions": sub_questions,
        "total_tokens": state.total_tokens + result.tokens_used,
        "total_latency_ms": state.total_latency_ms + latency_ms,
        "trace_logs": state.trace_logs + [trace_entry]
    }
