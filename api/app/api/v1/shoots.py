"""Shoot management — multi-admin per shoot.

- Owner: sees all shoots, can create/update any
- Admin: sees shoots where they have shoot_role=admin
- Tech/User: sees shoots they have access to
"""
import uuid
import secrets
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, require_admin, check_shoot_admin, check_shoot_access
from app.models.user import User
from app.models.shoot import Shoot
from app.models.shoot_access import ShootAccess
from app.schemas.shoot import (
    ShootCreate, ShootUpdate, ShootResponse, ShootListResponse,
    AccessCodeResponse, GenerateCodesRequest,
)

router = APIRouter(prefix="/shoots", tags=["Shoots"])


@router.post("", response_model=ShootResponse, status_code=status.HTTP_201_CREATED)
async def create_shoot(
    data: ShootCreate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Owner or Admin creates a shoot. Creator gets admin access automatically."""
    ssid = f"WFC-{data.name.replace(' ', '')[:20]}"
    shoot = Shoot(
        name=data.name, ssid=ssid, client=data.client, location=data.location,
        start_date=data.start_date, end_date=data.end_date, kit_id=data.kit_id,
        status="scheduled", created_by=current_user.id,
    )
    db.add(shoot)
    await db.flush()

    # Auto-grant admin access to creator
    code = secrets.token_urlsafe(6).upper()[:8]
    access = ShootAccess(
        shoot_id=shoot.id,
        user_id=current_user.id,
        shoot_role="admin",
        access_code=code,
        qr_data=f"wfc://{shoot.id}/{code}",
    )
    db.add(access)
    await db.commit()
    await db.refresh(shoot)
    return shoot


@router.get("", response_model=ShootListResponse)
async def list_shoots(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status"),
):
    """Owner sees all. Others see shoots they have access to."""
    if current_user.role == "owner":
        query = select(Shoot)
    else:
        # All roles (admin/tech/user) see shoots via ShootAccess
        query = (
            select(Shoot).distinct()
            .join(ShootAccess, ShootAccess.shoot_id == Shoot.id)
            .where(ShootAccess.user_id == current_user.id, ShootAccess.revoked_at.is_(None))
        )

    if status_filter:
        query = query.where(Shoot.status == status_filter)

    result = await db.execute(query.order_by(Shoot.created_at.desc()).limit(50))
    shoots = result.scalars().all()
    return ShootListResponse(shoots=shoots, total=len(shoots))


@router.get("/{shoot_id}", response_model=ShootResponse)
async def get_shoot(
    shoot_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Shoot).where(Shoot.id == shoot_id))
    shoot = result.scalar_one_or_none()
    if not shoot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shoot not found")

    if not await check_shoot_access(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this shoot")

    return shoot


@router.patch("/{shoot_id}", response_model=ShootResponse)
async def update_shoot(
    shoot_id: uuid.UUID,
    data: ShootUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update shoot — must be shoot admin or owner."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shoot admin access required")

    result = await db.execute(select(Shoot).where(Shoot.id == shoot_id))
    shoot = result.scalar_one_or_none()
    if not shoot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shoot not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(shoot, field, value)
    await db.commit()
    await db.refresh(shoot)
    return shoot


@router.post("/{shoot_id}/access-codes", response_model=list[AccessCodeResponse])
async def generate_access_codes(
    shoot_id: uuid.UUID,
    data: GenerateCodesRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generate access codes — shoot admins and owner."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shoot admin access required")

    codes = []
    for _ in range(data.count):
        code = secrets.token_urlsafe(6).upper()[:8]
        qr_data = f"wfc://{shoot_id}/{code}"
        db.add(ShootAccess(shoot_id=shoot_id, access_code=code, qr_data=qr_data))
        codes.append(AccessCodeResponse(code=code, qr_data=qr_data, shoot_id=shoot_id))
    await db.commit()
    return codes


@router.get("/{shoot_id}/members")
async def list_shoot_members(
    shoot_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all members of a shoot with their roles."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shoot admin access required")

    result = await db.execute(
        select(ShootAccess, User)
        .join(User, User.id == ShootAccess.user_id)
        .where(ShootAccess.shoot_id == shoot_id, ShootAccess.revoked_at.is_(None))
    )
    members = []
    for access, user in result.all():
        members.append({
            "user_id": str(user.id),
            "email": user.email,
            "name": user.name,
            "shoot_role": access.shoot_role,
            "granted_at": access.granted_at.isoformat() if access.granted_at else None,
        })
    return {"shoot_id": str(shoot_id), "members": members, "total": len(members)}
