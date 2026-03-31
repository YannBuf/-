"""Session management using Redis."""
import uuid
import json
from datetime import timedelta
from typing import Optional
import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()

# Redis connection pool
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=10,
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    """Get Redis connection."""
    return redis.Redis(connection_pool=redis_pool)


async def create_session(user_id: int, email: str, role: str = "owner") -> str:
    """Create a new session and return session token."""
    session_token = str(uuid.uuid4())
    session_data = {
        "user_id": user_id,
        "email": email,
        "role": role,
    }

    redis_client = await get_redis()
    await redis_client.setex(
        f"session:{session_token}",
        timedelta(days=7),
        json.dumps(session_data),
    )
    await redis_client.aclose()

    return session_token


async def get_session(session_token: str) -> Optional[dict]:
    """Get session data from session token. Returns None if expired/not found."""
    if not session_token:
        return None

    redis_client = await get_redis()
    data = await redis_client.get(f"session:{session_token}")
    await redis_client.aclose()

    if data:
        return json.loads(data)
    return None


async def delete_session(session_token: str) -> bool:
    """Delete a session (logout). Returns True if deleted."""
    if not session_token:
        return False

    redis_client = await get_redis()
    result = await redis_client.delete(f"session:{session_token}")
    await redis_client.aclose()

    return result > 0


async def refresh_session(session_token: str) -> bool:
    """Refresh session expiry. Returns True if session exists."""
    if not session_token:
        return False

    redis_client = await get_redis()
    result = await redis_client.expire(f"session:{session_token}", timedelta(days=7))
    await redis_client.aclose()

    return result
