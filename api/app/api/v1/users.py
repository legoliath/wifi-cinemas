"""User management — simplified 3 roles (owner/admin/user).

- Owner: see all users, create admins, deactivate anyone
- Admin: manage users on their shoot (via invitations)
- User: see themselves
"""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, require_owner, check_shoot_admin
from app.models.user import User
from app.models.shoot_access import ShootAccess
from app.schemas.user import UserResponse, UserUpdate, UserListResponse, UserCreate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user


# ── Owner: global ──────────────────────────────────────────────────────

@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    if current_user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(User))
    return UserListResponse(users=users, total=count_result.scalar() or 0)


@router.post("/admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin(
    data: UserCreate,
    owner: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Owner creates admin accounts (client onboarding)."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=data.email, name=data.name, phone=data.phone, role="admin", lang=data.lang)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: uuid.UUID,
    owner: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role == "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot deactivate an owner")
    user.is_active = False
    await db.commit()


# ── Admin: shoot-scoped ───────────────────────────────────────────────

@router.delete("/shoot/{shoot_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_shoot_member(
    shoot_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin removes a user from their shoot."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your shoot")

    from datetime import datetime, timezone
    result = await db.execute(
        select(ShootAccess).where(
            ShootAccess.shoot_id == shoot_id,
            ShootAccess.user_id == user_id,
            ShootAccess.revoked_at.is_(None),
        )
    )
    access = result.scalar_one_or_none()
    if not access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not in this shoot")
    access.revoked_at = datetime.now(timezone.utc)
    await db.commit()
