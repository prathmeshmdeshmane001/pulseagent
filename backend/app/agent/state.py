from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.evidence import Evidence

class SubQuestion(BaseModel):
    id: str = Field(..., description="Unique sub-question ID")
    text: str = Field(..., description="Targeted sub-question text")
    sources: List[str] = Field(..., description="Target source tools: notion, gmail, jira")

class AgentState(BaseModel):
    query: str
    session_id: str = "default_session"
    user_id: str = "default_user"
    
    # Milestone 2: Decomposition & multi-source
    sub_questions: List[SubQuestion] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    
    # Milestone 3: Memory
    memories: List[str] = Field(default_factory=list)
    
    # Milestone 5: Guardrails
    guardrail_blocked: bool = False
    guardrail_reason: Optional[str] = None
    citation_pass_rate: float = 1.0
    pending_action: Optional[Dict[str, Any]] = None
    
    # Synthesis & final output
    draft_answer: str = ""
    final_answer: str = ""
    claims: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 1.0

    # Milestone 4: Observability
    trace_logs: List[Dict[str, Any]] = Field(default_factory=list)
    total_tokens: int = 0
    total_latency_ms: int = 0
