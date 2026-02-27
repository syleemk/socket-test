import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://chatuser:chatpass@localhost:5432/chatdb",
)

REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "*").split(",")

REDIS_CHANNEL: str = os.getenv("REDIS_CHANNEL", "chat:channel")
REDIS_ONLINE_USERS_KEY: str = os.getenv("REDIS_ONLINE_USERS_KEY", "chat:online_users")

MESSAGE_HISTORY_LIMIT: int = int(os.getenv("MESSAGE_HISTORY_LIMIT", "50"))
