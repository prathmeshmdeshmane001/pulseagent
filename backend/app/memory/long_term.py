import json
import math
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.db_models import LongTermMemory

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def simple_embed(text: str, dim: int = 64) -> List[float]:
    """
    Lightweight deterministic local embedding function for offline/local vector similarity.
    Can be seamlessly swapped with Gemini text-embedding-004.
    """
    vec = [0.0] * dim
    words = text.lower().split()
    for w in words:
        h = hash(w)
        idx = abs(h) % dim
        vec[idx] += 1.0
    # Normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec

async def retrieve_long_term_memories(
    query: str,
    user_id: str,
    db: AsyncSession,
    top_k: int = 3
) -> List[str]:
    stmt = select(LongTermMemory).where(LongTermMemory.user_id == user_id)
    res = await db.execute(stmt)
    records = res.scalars().all()

    if not records:
        return []

    query_vec = simple_embed(query)
    scored = []

    for r in records:
        score = 0.0
        if r.embedding_json:
            try:
                emb = json.loads(r.embedding_json)
                score = cosine_similarity(query_vec, emb)
            except Exception:
                score = 0.0
        
        # Also compute word overlap keyword score
        query_words = set(query.lower().split())
        fact_words = set(r.fact.lower().split())
        overlap = len(query_words.intersection(fact_words))
        score += (overlap * 0.2)

        scored.append((score, r.fact))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [fact for score, fact in scored[:top_k] if score > 0.05]
