import json
from datetime import datetime, timezone
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.agent.llm_client import llm_client
from app.models.db_models import LongTermMemory
from app.memory.long_term import simple_embed

async def extract_and_store_facts(
    query: str,
    final_answer: str,
    session_id: str,
    user_id: str,
    db: AsyncSession
) -> List[str]:
    """
    Extracts 0 to 3 durable, high-value reusable facts worth persisting across sessions.
    Writes durable facts with embeddings into long_term_memory.
    """
    prompt = (
        f"You are the long-term memory extraction node of PulseAgent.\n"
        f"Analyze the following user query and final answer.\n"
        f"Extract 0 to 3 durable, high-value, reusable facts about the user's project, priorities, or decisions.\n"
        f"Only extract facts that are valuable across future sessions (e.g., 'Project X deadline is Q3', 'User priority is privacy').\n"
        f"Do NOT extract transient status updates, chat greetings, or temporary questions.\n\n"
        f"User Query: {query}\n"
        f"Final Answer: {final_answer}\n\n"
        f"Return JSON:\n"
        f'{{\n  "facts": ["fact 1", "fact 2"]\n}}'
    )

    result = await llm_client.generate_gemini(prompt=prompt, json_mode=True, temperature=0.1)
    
    extracted_facts: List[str] = []
    try:
        data = json.loads(result.text)
        facts = data.get("facts", [])
        for f in facts:
            if isinstance(f, str) and len(f.strip()) > 5:
                extracted_facts.append(f.strip())
    except Exception:
        pass

    stored_facts: List[str] = []
    for fact in extracted_facts[:3]:
        emb = simple_embed(fact)
        record = LongTermMemory(
            user_id=user_id,
            fact=fact,
            source_session_id=session_id,
            embedding_json=json.dumps(emb),
            created_at=datetime.now(timezone.utc)
        )
        db.add(record)
        stored_facts.append(fact)

    if stored_facts:
        await db.commit()

    return stored_facts
