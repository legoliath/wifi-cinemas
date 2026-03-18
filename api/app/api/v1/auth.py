from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.shoot_access import ShootAccess
from app.schemas.auth import LoginRequest, RegisterRequest, InviteCodeRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

def create_access_token(user_id: str, role: str) -> tuple[str, int]:
    expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta
    token = jwt.encode({"sub": user_id, "role": role, "exp": expire}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(expires_delta.total_seconds())

@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    shoot_access = None
    if data.invite_code:
        result = await db.execute(select(ShootAccess).where(ShootAccess.access_code == data.invite_code, ShootAccess.user_id.is_(None), ShootAccess.revoked_at.is_(None)))
        shoot_access = result.scalar_one_or_none()
        if not shoot_access:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or used invite code")
    user = User(email=data.email, name=data.name, role="user", lang=data.lang)
    db.add(user)
    await db.flush()
    if shoot_access:
        shoot_access.user_id = user.id
    await db.commit()
    await db.refresh(user)
    token, expires_in = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=token, expires_in=expires_in, user_id=str(user.id), role=user.role)

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")
    token, expires_in = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=token, expires_in=expires_in, user_id=str(user.id), role=user.role)

@router.post("/verify-invite-code")
async def verify_invite_code(data: InviteCodeRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(ShootAccess).where(ShootAccess.access_code == data.code, ShootAccess.user_id.is_(None), ShootAccess.revoked_at.is_(None)))
    access = result.scalar_one_or_none()
    if not access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or used code")
    return {"valid": True, "shoot_id": str(access.shoot_id)}
