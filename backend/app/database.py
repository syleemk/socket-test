from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    # Schema is managed by Alembic. Run: uv run alembic upgrade head
    pass
