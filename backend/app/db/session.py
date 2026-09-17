import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.base import Base
# Import all models so metadata knows about them
import app.models.db_models # noqa: F401

load_dotenv()

raw_db_url = os.getenv("DATABASE_URL", "").strip()

if not raw_db_url:
    # Anchor SQLite database path to backend directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    db_file = os.path.join(base_dir, "pulseagent.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{db_file}"
elif raw_db_url.startswith("sqlite+aiosqlite:///./"):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    filename = raw_db_url.replace("sqlite+aiosqlite:///./", "")
    db_file = os.path.join(base_dir, filename)
    DATABASE_URL = f"sqlite+aiosqlite:///{db_file}"
elif raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif raw_db_url.startswith("postgresql://") and not raw_db_url.startswith("postgresql+"):
    DATABASE_URL = raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = raw_db_url

engine_args = {}
if "sqlite" in DATABASE_URL:
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(DATABASE_URL, echo=False, **engine_args)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
