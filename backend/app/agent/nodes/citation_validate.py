import time
import re
from typing import List, Tuple
from app.agent.state import AgentState
from app.agent.llm_client import llm_client

CITATION_REGEX = re.compile(r'\[(\d+)\]')

async def citation_validate_node(state: AgentState) -> dict:
    start_time = time.perf_counter()

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', state.draft_answer) if s.strip()]
    
    total_citations = 0
    passed_citations = 0
    tokens_used = 0

    for sentence in sentences:
        indices = [int(m) for m in CITATION_REGEX.findall(sentence)]
        if not indices:
            continue

        for idx in indices:
            total_citations += 1
            if 1 <= idx <= len(state.evidence):
                ev = state.evidence[idx - 1]
                prompt = (
                    "You are a citation entailment judge.\n"
                    "Determine whether the given evidence excerpt supports the specified claim.\n"
                    "Answer ONLY 'yes' if supported, or 'no' if unsupported or contradictory.\n\n"
                    f"Evidence: {ev.snippet}\n"
                    f"Claim: {sentence}"
                )
                result = await llm_client.generate_groq(prompt=prompt)
                tokens_used += result.tokens_used
                if "yes" in result.text.lower():
                    passed_citations += 1
            else:
                # Invalid citation index
                pass

    pass_rate = (passed_citations / total_citations) if total_citations > 0 else 1.0
    latency_ms = int((time.perf_counter() - start_time) * 1000)

    trace_entry = {
        "node_name": "citation_validate",
        "input_summary": f"Validated {total_citations} citations in draft answer",
        "output_summary": f"Citation entailment score: {passed_citations}/{total_citations} passed ({pass_rate * 100:.1f}%)",
        "tokens_used": tokens_used,
        "latency_ms": latency_ms
    }

    return {
        "citation_pass_rate": pass_rate,
        "total_tokens": state.total_tokens + tokens_used,
        "total_latency_ms": state.total_latency_ms + latency_ms,
        "trace_logs": state.trace_logs + [trace_entry]
    }
