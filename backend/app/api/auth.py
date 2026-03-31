from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.services.auth import create_user, authenticate_user, generate_token, logout_user
from app.services.session import get_session

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        user = await create_user(db, user_data)
        return user
    except Exception as e:
        if "unique" in str(e).lower():
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return await generate_token(user)


@router.post("/logout")
async def logout(authorization: str = Header(None)):
    """Logout user by deleting session."""
    if authorization:
        try:
            scheme, token = authorization.split()
            if scheme.lower() == "bearer":
                await logout_user(token)
        except ValueError:
            pass
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(authorization: str = Header(None)):
    """Get current user from session token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    session_data = await get_session(token)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return UserResponse(
        id=session_data["user_id"],
        email=session_data["email"],
        role=session_data.get("role", "owner"),
    )