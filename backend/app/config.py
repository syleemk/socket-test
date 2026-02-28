import os
from dotenv import load_dotenv

load_dotenv()

DB_USER: str = os.getenv("DB_USER", "")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: str = os.getenv("DB_PORT", "5432")
DB_NAME: str = os.getenv("DB_NAME", "chatdb")

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)

REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")

REDIS_CHANNEL: str = os.getenv("REDIS_CHANNEL", "chat:channel")
REDIS_ONLINE_USERS_KEY: str = os.getenv("REDIS_ONLINE_USERS_KEY", "chat:online_users")

MESSAGE_HISTORY_LIMIT: int = int(os.getenv("MESSAGE_HISTORY_LIMIT", "50"))
