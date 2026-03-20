"""User management — 5 roles with hierarchy enforcement.

- Owner: see all users, create super_admins, deactivate anyone
- Super admin (1 per shoot): add admins + techs to their shoot
- Admin: add techs + crew to their shoot
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

# What each shoot_role can add
_ADD_PERMISSIONS = {
    "super_admin": {"admin", "tech", "user"},
    "admin": {"tech", "user"},
}


async def _get_shoot_role(user: User, shoot_id: uuid.UUID, db: AsyncSession) -> str | None:
    """Get user's shoot_role for a specific shoot. Returns None if no access."""
    if user.role == "owner":
        return "owner"
    result = await db.execute(
        select(ShootAccess.shoot_role).where(
            ShootAccess.shoot_id == shoot_id,
            ShootAccess.user_id == user.id,
            ShootAccess.revoked_at.is_(None),
        )
    )
    row = result.scalar_one_or_none()
    return row


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
    """Owner creates admin / super_admin accounts."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    role = data.role if data.role in ("admin", "super_admin") else "admin"
    user = User(email=data.email, name=data.name, phone=data.phone, role=role, lang=data.lang)
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


# ── Shoot-scoped member management ────────────────────────────────────

@router.post("/shoot/{shoot_id}/members", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def add_shoot_member(
    shoot_id: uuid.UUID,
    data: UserCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add member with role enforcement:
    - Owner: can add super_admin, admin, tech, user
    - Super admin: can add admin, tech, user
    - Admin: can add tech, user only
    - Super admin is unique per shoot (enforced)
    """
    caller_shoot_role = await _get_shoot_role(current_user, shoot_id, db)

    if caller_shoot_role == "owner":
        allowed = {"super_admin", "admin", "tech", "user"}
    elif caller_shoot_role in _ADD_PERMISSIONS:
        allowed = _ADD_PERMISSIONS[caller_shoot_role]
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot add members to this shoot")

    target_role = data.role if data.role in allowed else None
    if not target_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your role ({caller_shoot_role}) cannot add '{data.role}'. Allowed: {', '.join(sorted(allowed))}",
        )

    # Enforce: only 1 super_admin per shoot
    if target_role == "super_admin":
        existing_sa = await db.execute(
            select(ShootAccess).where(
                ShootAccess.shoot_id == shoot_id,
                ShootAccess.shoot_role == "super_admin",
                ShootAccess.revoked_at.is_(None),
            )
        )
        if existing_sa.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This shoot already has a super admin",
            )

    # Find or create user
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        global_role = target_role if target_role in ("super_admin", "admin") else data.role
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
    """Remove member. Super admin can remove admins. Admin can remove tech/user."""
    caller_shoot_role = await _get_shoot_role(current_user, shoot_id, db)

    if caller_shoot_role not in ("owner", "super_admin", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot remove members")

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

    # Role removal check: can't remove someone at/above your level (unless owner)
    role_level = {"owner": 5, "super_admin": 4, "admin": 3, "tech": 2, "user": 1}
    caller_level = role_level.get(caller_shoot_role, 0)
    target_level = role_level.get(access.shoot_role, 0)

    if caller_shoot_role != "owner" and target_level >= caller_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot remove a {access.shoot_role} (same or higher level)",
        )

    access.revoked_at = datetime.now(timezone.utc)
    await db.commit()
