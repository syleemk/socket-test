import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import CORS_ORIGINS
from app.database import engine, init_db
from app.infrastructure.pubsub import redis_subscriber
from app.infrastructure.redis import get_redis
from app.routers import channels, chat


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    task = asyncio.create_task(redis_subscriber())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    redis = get_redis()
    await redis.aclose()  # type: ignore[attr-defined]


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(channels.router)


async def _check_redis() -> str:
    try:
        await get_redis().ping()
        return "ok"
    except Exception:
        return "error"


async def _check_postgres() -> str:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


@app.get("/health")
async def health(response: Response) -> dict[str, str]:
    redis_status, postgres_status = await asyncio.gather(_check_redis(), _check_postgres())

    ok = redis_status == "ok" and postgres_status == "ok"
    if not ok:
        response.status_code = 503

    return {
        "redis": redis_status,
        "postgres": postgres_status,
        "status": "ok" if ok else "error",
    }
