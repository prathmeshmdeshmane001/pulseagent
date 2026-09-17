from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from app.db.base import Base
from app.db.session import engine

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if using local SQLite / development
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(
    title="PulseAgent API",
    description="Agentic RAG assistant over Gmail, Notion, Jira with guardrails, memory, and observability",
    version="0.1.0",
    lifespan=lifespan
)

origins = [
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.auth.router import router as auth_router
from app.agent.router import router as agent_router
from app.agent.actions_router import router as actions_router

app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(actions_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/metrics")
async def get_metrics():
    # Lightweight metrics endpoint as specified in build guide section 7
    return {
        "status": "healthy",
        "service": "pulseagent-backend",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
