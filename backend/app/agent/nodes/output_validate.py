import time
import re
from typing import List, Optional
from pydantic import BaseModel, Field
from app.agent.state import AgentState

class Claim(BaseModel):
    text: str
    citation_indices: List[int] = Field(default_factory=list)

class Citation(BaseModel):
    index: int
    source: str
    permalink: str
    snippet: str

class AgentResponseSchema(BaseModel):
    claims: List[Claim]
    citations: List[Citation]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

CITATION_REGEX = re.compile(r'\[(\d+)\]')

async def output_validate_node(state: AgentState) -> dict:
    start_time = time.perf_counter()

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', state.draft_answer) if s.strip()]
    claims: List[Claim] = []
    citations_map = {}

    for s in sentences:
        indices = [int(m) for m in CITATION_REGEX.findall(s)]
        claims.append(Claim(text=s, citation_indices=indices))
        for idx in indices:
            if 1 <= idx <= len(state.evidence) and idx not in citations_map:
                ev = state.evidence[idx - 1]
                citations_map[idx] = Citation(
                    index=idx,
                    source=ev.source,
                    permalink=ev.permalink,
                    snippet=ev.snippet[:100]
                )

    citations_list = sorted(citations_map.values(), key=lambda c: c.index)
    confidence = min(1.0, max(0.5, state.citation_pass_rate))

    # Validate against schema
    validated = AgentResponseSchema(
        claims=claims,
        citations=citations_list,
        confidence=confidence
    )

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    trace_entry = {
        "node_name": "output_validate",
        "input_summary": f"Inspected {len(claims)} claims and {len(citations_list)} citations",
        "output_summary": f"Schema validation PASSED. Confidence: {confidence:.2f}",
        "tokens_used": 0,
        "latency_ms": latency_ms
    }

    return {
        "claims": [c.model_dump() for c in claims],
        "confidence": confidence,
        "total_latency_ms": state.total_latency_ms + latency_ms,
        "trace_logs": state.trace_logs + [trace_entry]
    }
