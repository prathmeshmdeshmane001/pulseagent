import os
import time
from datetime import datetime, timezone
from app.agent.state import AgentState
from app.db.session import AsyncSessionLocal
from app.models.db_models import PendingAction

RISKY_ACTION_PATTERNS = [
    "delete jira ticket",
    "archive notion page",
    "send email on user's behalf",
    "delete page",
    "drop table",
    "delete project",
    "cancel sprint",
    "modify permissions"
]

async def permission_gate_node(state: AgentState) -> dict:
    start_time = time.perf_counter()

    combined_text = (state.query + " " + state.draft_answer).lower()
    detected_risky_action = None

    for pattern in RISKY_ACTION_PATTERNS:
        if pattern in combined_text:
            detected_risky_action = pattern
            break

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    if detected_risky_action:
        async with AsyncSessionLocal() as db:
            action_record = PendingAction(
                session_id=state.session_id,
                action_description=f"Action requested: {detected_risky_action}",
                status="pending",
                created_at=datetime.now(timezone.utc)
            )
            db.add(action_record)
            await db.commit()
            await db.refresh(action_record)
            action_id = action_record.id

        confirmation_msg = (
            f"I have identified a sensitive operation ('{detected_risky_action}'). "
            f"For security, I've prepared action #{action_id} and placed it in pending verification. "
            f"A confirmation email has been triggered. Please approve via /actions/{action_id}/approve or deny via /actions/{action_id}/deny before this action can proceed."
        )

        trace_entry = {
            "node_name": "permission_gate",
            "input_summary": f"Detected risky pattern: '{detected_risky_action}'",
            "output_summary": f"Action #{action_id} GATED. Pending approval.",
            "tokens_used": 0,
            "latency_ms": latency_ms
        }

        return {
            "final_answer": confirmation_msg,
            "pending_action": {"id": action_id, "description": detected_risky_action, "status": "pending"},
            "total_latency_ms": state.total_latency_ms + latency_ms,
            "trace_logs": state.trace_logs + [trace_entry]
        }

    trace_entry = {
        "node_name": "permission_gate",
        "input_summary": "Evaluated action permissions",
        "output_summary": "No risky actions detected. Safe to proceed.",
        "tokens_used": 0,
        "latency_ms": latency_ms
    }

    return {
        "total_latency_ms": state.total_latency_ms + latency_ms,
        "trace_logs": state.trace_logs + [trace_entry]
    }
