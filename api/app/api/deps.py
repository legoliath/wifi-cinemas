import uuid
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User deactivated")
    return user


async def require_owner(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    return current_user


async def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Owner or admin."""
    if current_user.role not in ("owner", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def check_shoot_admin(user: User, shoot_id: uuid.UUID, db: AsyncSession) -> bool:
    """Is this user owner, or the admin of this shoot?"""
    if user.role == "owner":
        return True
    if user.role != "admin":
        return False
    from app.models.shoot_access import ShootAccess
    result = await db.execute(
        select(ShootAccess).where(
            ShootAccess.shoot_id == shoot_id,
            ShootAccess.user_id == user.id,
            ShootAccess.revoked_at.is_(None),
        )
    )
    return result.scalar_one_or_none() is not None


async def check_shoot_access(user: User, shoot_id: uuid.UUID, db: AsyncSession) -> bool:
    """Does this user have any access to this shoot?"""
    if user.role == "owner":
        return True
    from app.models.shoot_access import ShootAccess
    result = await db.execute(
        select(ShootAccess).where(
            ShootAccess.shoot_id == shoot_id,
            ShootAccess.user_id == user.id,
            ShootAccess.revoked_at.is_(None),
        )
    )
    return result.scalar_one_or_none() is not None
