import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.schemas.datasource import DataSourceCreate, DataSourceResponse
from app.services.datasource import create_datasource, get_user_datasources, get_datasource, upload_and_parse
from app.services.session import get_session
from app.config import get_settings
from app.schemas.auth import UserResponse
from typing import List, Dict, Any

router = APIRouter()


async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Extract current user from session token in Authorization header.
    """
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


@router.post("/", status_code=201)
async def create_file_datasource(
    name: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    print(f"[UPLOAD] user_id from token: {current_user.id}")
    # Validate file type using settings.ALLOWED_EXTENSIONS
    settings = get_settings()
    ext = os.path.splitext(file.filename)[1] if file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {settings.ALLOWED_EXTENSIONS}")

    result = await upload_and_parse(db, user_id=current_user.id, file=file, name=name)
    return result


@router.get("/", response_model=List[DataSourceResponse])
async def list_datasources(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_user_datasources(db, user_id=current_user.id)


@router.get("/{datasource_id}", response_model=DataSourceResponse)
async def get_datasource_by_id(
    datasource_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    datasource = await get_datasource(db, datasource_id, user_id=current_user.id)
    if not datasource:
        raise HTTPException(status_code=404, detail="Data source not found")
    return datasource
