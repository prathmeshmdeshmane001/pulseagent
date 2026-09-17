import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.evidence import Evidence
from app.models.db_models import RunTrace, SessionModel, MessageModel
from app.agent.graph import run_agent

router = APIRouter(tags=["chat"])

class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "default_user"

class SubQuestionResponse(BaseModel):
    id: str
    text: str
    sources: List[str]

class ChatResponse(BaseModel):
    answer: str
    evidence: List[Evidence]
    session_id: str
    guardrail_blocked: bool = False
    refusal_reason: Optional[str] = None
    sub_questions: List[SubQuestionResponse] = []
    memories_used: List[str] = []
    total_tokens: int = 0
    total_latency_ms: int = 0

class TraceStepResponse(BaseModel):
    id: Optional[int] = None
    session_id: str
    node_name: str
    input_summary: str
    output_summary: str
    tokens_used: int
    latency_ms: int
    created_at: Optional[str] = None

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    session_id = payload.query.strip() if payload.session_id is None else payload.session_id
    if not session_id or session_id == payload.query.strip():
        session_id = f"sess_{uuid.uuid4().hex[:8]}"

    # Ensure session exists in DB
    existing_session = await db.get(SessionModel, session_id)
    if not existing_session:
        new_session = SessionModel(id=session_id, user_id=payload.user_id or "default_user")
        db.add(new_session)
        await db.commit()

    # Save user message
    user_msg = MessageModel(session_id=session_id, role="user", content=payload.query)
    db.add(user_msg)
    await db.commit()

    # Run agent graph
    state = await run_agent(query=payload.query, session_id=session_id, user_id=payload.user_id or "default_user")

    # Persist trace logs into run_traces table
    for t in state.trace_logs:
        trace_record = RunTrace(
            session_id=session_id,
            node_name=t.get("node_name", "unknown"),
            input_summary=t.get("input_summary", ""),
            output_summary=t.get("output_summary", ""),
            tokens_used=t.get("tokens_used", 0),
            latency_ms=t.get("latency_ms", 0)
        )
        db.add(trace_record)

    # Save assistant message
    asst_msg = MessageModel(session_id=session_id, role="assistant", content=state.final_answer)
    db.add(asst_msg)
    await db.commit()

    sub_qs = [
        SubQuestionResponse(
            id=getattr(sq, "id", f"sq_{i}"),
            text=getattr(sq, "text", str(sq)),
            sources=getattr(sq, "sources", ["all"])
        )
        for i, sq in enumerate(state.sub_questions, 1)
    ]

    return ChatResponse(
        answer=state.final_answer,
        evidence=state.evidence,
        session_id=session_id,
        guardrail_blocked=state.guardrail_blocked,
        refusal_reason=state.guardrail_reason,
        sub_questions=sub_qs,
        memories_used=state.memories,
        total_tokens=state.total_tokens,
        total_latency_ms=state.total_latency_ms
    )

@router.get("/trace/{session_id}", response_model=List[TraceStepResponse])
async def get_trace_endpoint(session_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(RunTrace).where(RunTrace.session_id == session_id).order_by(RunTrace.id.asc())
    res = await db.execute(stmt)
    traces = res.scalars().all()
    return [
        TraceStepResponse(
            id=t.id,
            session_id=t.session_id,
            node_name=t.node_name,
            input_summary=t.input_summary,
            output_summary=t.output_summary,
            tokens_used=t.tokens_used,
            latency_ms=t.latency_ms,
            created_at=t.created_at.isoformat() if t.created_at else None
        )
        for t in traces
    ]
