"""
Migrate all PulseAgent data from local SQLite to remote Supabase PostgreSQL.
Preserves live OAuth tokens, sessions, messages, memory, and traces.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Ensure backend root is in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text
from app.db.base import Base
from app.models.db_models import (
    OAuthToken,
    SessionModel,
    MessageModel,
    LongTermMemory,
    RunTrace,
    PendingAction,
)

SQLITE_PATH = os.path.join(BASE_DIR, "pulseagent.db")
SQLITE_URL = f"sqlite+aiosqlite:///{SQLITE_PATH}"

def normalize_pg_url(url: str) -> str:
    url = url.strip()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

async def migrate(target_url: str):
    norm_target_url = normalize_pg_url(target_url)
    display_url = norm_target_url.split('@')[-1] if '@' in norm_target_url else norm_target_url
    print(f"Connecting to SQLite: {SQLITE_URL}")
    print(f"Connecting to PostgreSQL: {display_url}")

    sqlite_engine = create_async_engine(SQLITE_URL, echo=False)
    pg_engine = create_async_engine(norm_target_url, echo=False)

    SqliteSession = async_sessionmaker(bind=sqlite_engine, class_=AsyncSession, expire_on_commit=False)
    PgSession = async_sessionmaker(bind=pg_engine, class_=AsyncSession, expire_on_commit=False)

    print("\n1. Ensuring PostgreSQL tables exist...")
    async with pg_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("   Tables created / verified in PostgreSQL.")

    print("\n2. Reading data from SQLite...")
    async with SqliteSession() as s_db:
        oauth_tokens = (await s_db.execute(select(OAuthToken))).scalars().all()
        sessions = (await s_db.execute(select(SessionModel))).scalars().all()
        messages = (await s_db.execute(select(MessageModel))).scalars().all()
        memories = (await s_db.execute(select(LongTermMemory))).scalars().all()
        traces = (await s_db.execute(select(RunTrace))).scalars().all()
        actions = (await s_db.execute(select(PendingAction))).scalars().all()

    print(f"   Fetched {len(oauth_tokens)} oauth_tokens")
    print(f"   Fetched {len(sessions)} sessions")
    print(f"   Fetched {len(messages)} messages")
    print(f"   Fetched {len(memories)} memories")
    print(f"   Fetched {len(traces)} traces")
    print(f"   Fetched {len(actions)} actions")

    print("\n3. Inserting data into PostgreSQL...")
    async with PgSession() as p_db:
        # Sessions first (messages and others foreign key / reference session_id)
        for s in sessions:
            existing = await p_db.get(SessionModel, s.id)
            if not existing:
                p_db.add(SessionModel(id=s.id, user_id=s.user_id, created_at=s.created_at))
        await p_db.commit()

        # OAuth tokens
        for t in oauth_tokens:
            existing = (await p_db.execute(
                select(OAuthToken).where(
                    OAuthToken.user_id == t.user_id,
                    OAuthToken.provider == t.provider
                )
            )).scalars().first()
            if not existing:
                p_db.add(OAuthToken(
                    user_id=t.user_id,
                    provider=t.provider,
                    access_token_encrypted=t.access_token_encrypted,
                    refresh_token_encrypted=t.refresh_token_encrypted,
                    expires_at=t.expires_at,
                    created_at=t.created_at
                ))
            else:
                existing.access_token_encrypted = t.access_token_encrypted
                existing.refresh_token_encrypted = t.refresh_token_encrypted
                existing.expires_at = t.expires_at
        await p_db.commit()

        # Messages
        for m in messages:
            p_db.add(MessageModel(
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                created_at=m.created_at
            ))
        await p_db.commit()

        # Memories
        for mem in memories:
            p_db.add(LongTermMemory(
                user_id=mem.user_id,
                fact=mem.fact,
                source_session_id=mem.source_session_id,
                embedding_json=mem.embedding_json,
                created_at=mem.created_at
            ))
        await p_db.commit()

        # Traces
        for tr in traces:
            p_db.add(RunTrace(
                session_id=tr.session_id,
                node_name=tr.node_name,
                input_summary=tr.input_summary,
                output_summary=tr.output_summary,
                tokens_used=tr.tokens_used,
                latency_ms=tr.latency_ms,
                created_at=tr.created_at
            ))
        await p_db.commit()

        # Pending Actions
        for a in actions:
            p_db.add(PendingAction(
                session_id=a.session_id,
                action_description=a.action_description,
                status=a.status,
                created_at=a.created_at
            ))
        await p_db.commit()

    # Reset postgres sequences
    print("\n4. Resetting PostgreSQL serial sequences...")
    async with pg_engine.begin() as conn:
        for table in ["oauth_tokens", "messages", "long_term_memory", "run_traces", "pending_actions"]:
            try:
                await conn.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), coalesce(max(id), 1)) FROM {table};"
                ))
            except Exception as e:
                print(f"   Note sequence reset for {table}: {e}")

    # Verify counts in PostgreSQL
    print("\n5. Verifying row counts in PostgreSQL...")
    async with PgSession() as p_db:
        t_count = (await p_db.execute(text("SELECT count(*) FROM oauth_tokens"))).scalar()
        s_count = (await p_db.execute(text("SELECT count(*) FROM sessions"))).scalar()
        m_count = (await p_db.execute(text("SELECT count(*) FROM messages"))).scalar()
        mem_count = (await p_db.execute(text("SELECT count(*) FROM long_term_memory"))).scalar()
        tr_count = (await p_db.execute(text("SELECT count(*) FROM run_traces"))).scalar()
        pa_count = (await p_db.execute(text("SELECT count(*) FROM pending_actions"))).scalar()

        print(f"   PostgreSQL oauth_tokens: {t_count}")
        print(f"   PostgreSQL sessions: {s_count}")
        print(f"   PostgreSQL messages: {m_count}")
        print(f"   PostgreSQL long_term_memory: {mem_count}")
        print(f"   PostgreSQL run_traces: {tr_count}")
        print(f"   PostgreSQL pending_actions: {pa_count}")

    await sqlite_engine.dispose()
    await pg_engine.dispose()
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = os.getenv("DATABASE_URL", "")

    if not target or "sqlite" in target:
        print("Usage: python backend/scripts/migrate_to_postgres.py <TARGET_POSTGRES_URL>")
        sys.exit(1)

    asyncio.run(migrate(target))
