from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import verify_password, get_password_hash
from app.schemas.auth import UserCreate, UserLogin, Token
from app.services.session import create_session, delete_session
from datetime import timedelta
from app.config import get_settings

settings = get_settings()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, credentials: UserLogin) -> User | None:
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(credentials.password, user.hashed_password):
        return None
    return user


async def generate_token(user: User) -> Token:
    """Generate session-based token."""
    session_token = await create_session(
        user_id=user.id,
        email=user.email,
        role=user.role.value if hasattr(user.role, 'value') else "owner",
    )
    return Token(access_token=session_token, refresh_token=None, token_type="session")


async def logout_user(session_token: str) -> bool:
    """Logout user by deleting session."""
    return await delete_session(session_token)