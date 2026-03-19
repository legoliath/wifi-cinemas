"""Shoot management.

- Owner: sees all shoots, can create/update any
- Admin: sees only shoots they created, can create new ones
- Tech/User: sees shoots they have access to
"""
import uuid
import secrets
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, require_admin
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
    admin: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Owner or Admin creates a shoot."""
    ssid = f"WFC-{data.name.replace(' ', '')[:20]}"
    shoot = Shoot(
        name=data.name, ssid=ssid, client=data.client, location=data.location,
        start_date=data.start_date, end_date=data.end_date, kit_id=data.kit_id,
        status="scheduled", created_by=admin.id,
    )
    db.add(shoot)
    await db.commit()
    await db.refresh(shoot)
    return shoot


@router.get("", response_model=ShootListResponse)
async def list_shoots(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = Query(None, alias="status"),
):
    """Owner sees all. Admin sees their shoots. Tech/User sees shoots they have access to."""
    if current_user.role == "owner":
        query = select(Shoot)
    elif current_user.role == "admin":
        query = select(Shoot).where(Shoot.created_by == current_user.id)
    else:
        # tech/user — only shoots they have access to
        query = (
            select(Shoot)
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
    """Get shoot — with access control."""
    result = await db.execute(select(Shoot).where(Shoot.id == shoot_id))
    shoot = result.scalar_one_or_none()
    if not shoot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shoot not found")

    # Owner sees everything
    if current_user.role == "owner":
        return shoot

    # Admin sees only their shoots
    if current_user.role == "admin":
        if shoot.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your shoot")
        return shoot

    # Tech/User — must have access
    access = await db.execute(
        select(ShootAccess).where(
            ShootAccess.shoot_id == shoot_id,
            ShootAccess.user_id == current_user.id,
            ShootAccess.revoked_at.is_(None),
        )
    )
    if not access.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this shoot")

    return shoot


@router.patch("/{shoot_id}", response_model=ShootResponse)
async def update_shoot(
    shoot_id: uuid.UUID,
    data: ShootUpdate,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update shoot — owner can update any, admin only their own."""
    result = await db.execute(select(Shoot).where(Shoot.id == shoot_id))
    shoot = result.scalar_one_or_none()
    if not shoot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shoot not found")

    if current_user.role != "owner" and shoot.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your shoot")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(shoot, field, value)
    await db.commit()
    await db.refresh(shoot)
    return shoot


@router.post("/{shoot_id}/access-codes", response_model=list[AccessCodeResponse])
async def generate_access_codes(
    shoot_id: uuid.UUID,
    data: GenerateCodesRequest,
    current_user: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generate access codes — admin for their shoot, owner for any."""
    # Verify ownership
    if current_user.role != "owner":
        result = await db.execute(
            select(Shoot).where(Shoot.id == shoot_id, Shoot.created_by == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your shoot")

    codes = []
    for _ in range(data.count):
        code = secrets.token_urlsafe(6).upper()[:8]
        qr_data = f"wfc://{shoot_id}/{code}"
        db.add(ShootAccess(shoot_id=shoot_id, access_code=code, qr_data=qr_data))
        codes.append(AccessCodeResponse(code=code, qr_data=qr_data, shoot_id=shoot_id))
    await db.commit()
    return codes
