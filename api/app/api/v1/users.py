"""User management — multi-admin per shoot.

- Owner: see all users, create admins, deactivate anyone
- Admin (shoot-level): add/remove members for shoots they admin
- Tech/User: see themselves only
"""
import uuid
import secrets
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, require_owner, check_shoot_admin
from app.models.user import User
from app.models.shoot import Shoot
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


# ── Owner: global user management ──────────────────────────────────────

@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Owner sees all users."""
    if current_user.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner access required")

    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar() or 0
    return UserListResponse(users=users, total=total)


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
    """Owner deactivates any user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role == "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot deactivate an owner")
    user.is_active = False
    await db.commit()


# ── Shoot-scoped member management (any shoot admin) ──────────────────

@router.post("/shoot/{shoot_id}/members", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def add_shoot_member(
    shoot_id: uuid.UUID,
    data: UserCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Shoot admin adds a member (admin, tech, or user) to their shoot."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shoot admin access required")

    # Validate role — shoot admins can add admin, tech, or user
    allowed_roles = ("admin", "tech", "user")
    target_role = data.role if data.role in allowed_roles else "user"

    # Find or create user
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        # Set global role: admin stays admin, tech/user stay as-is
        global_role = "admin" if target_role == "admin" else data.role
        user = User(email=data.email, name=data.name, phone=data.phone, role=global_role, lang=data.lang)
        db.add(user)
        await db.flush()

    # Check not already a member
    existing = await db.execute(
        select(ShootAccess).where(
            ShootAccess.shoot_id == shoot_id,
            ShootAccess.user_id == user.id,
            ShootAccess.revoked_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already has access to this shoot")

    code = secrets.token_urlsafe(6).upper()[:8]
    access = ShootAccess(
        shoot_id=shoot_id,
        user_id=user.id,
        shoot_role=target_role,
        access_code=code,
        qr_data=f"wfc://{shoot_id}/{code}",
    )
    db.add(access)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/shoot/{shoot_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_shoot_member(
    shoot_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Shoot admin removes a member (revokes access)."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shoot admin access required")

    # Can't remove yourself if you're the last admin
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

    # Safety: don't let last admin remove themselves
    if access.shoot_role == "admin" and user_id == current_user.id:
        admin_count_result = await db.execute(
            select(func.count()).select_from(ShootAccess).where(
                ShootAccess.shoot_id == shoot_id,
                ShootAccess.shoot_role == "admin",
                ShootAccess.revoked_at.is_(None),
            )
        )
        if (admin_count_result.scalar() or 0) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last admin from a shoot",
            )

    access.revoked_at = datetime.now(timezone.utc)
    await db.commit()
