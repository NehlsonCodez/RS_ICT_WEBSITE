import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.models import Base

# On Railway: mount a volume at /data and set DATA_DIR=/data
# On Render:  disk is mounted at /data via render.yaml
# Locally:    falls back to ./rs_ict.db in the project folder
_data_dir = os.environ.get("DATA_DIR", ".")
DATABASE_URL = f"sqlite+aiosqlite:///{_data_dir}/rs_ict.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """FastAPI dependency that yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
