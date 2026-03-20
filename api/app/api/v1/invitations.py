"""Email invitation system.

Flow:
1. Admin enters email → POST /invitations/shoot/{shoot_id}
2. Backend creates ShootAccess with invite_token, sends email
3. User clicks link → GET /invitations/accept/{token}
4. Account created (or linked), access granted, redirect to app
"""
import uuid
import secrets
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_current_user, check_shoot_admin
from app.models.user import User
from app.models.shoot import Shoot
from app.models.shoot_access import ShootAccess
from app.services.notification import send_invite_email

router = APIRouter(prefix="/invitations", tags=["Invitations"])


class InviteRequest(BaseModel):
    email: str
    name: str | None = None
    user_class: str | None = None  # tech, vip, chef_dep, etc.


class InviteResponse(BaseModel):
    invite_token: str
    invite_url: str
    email: str
    shoot_id: uuid.UUID
    user_class: str | None


class AcceptResponse(BaseModel):
    message: str
    user_id: uuid.UUID
    shoot_id: uuid.UUID
    shoot_name: str


@router.post("/shoot/{shoot_id}", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    shoot_id: uuid.UUID,
    data: InviteRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin invites a user to their shoot via email."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your shoot")

    # Check shoot exists
    shoot_result = await db.execute(select(Shoot).where(Shoot.id == shoot_id))
    shoot = shoot_result.scalar_one_or_none()
    if not shoot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shoot not found")

    # Check not already invited / has access
    existing = await db.execute(
        select(ShootAccess).where(
            ShootAccess.shoot_id == shoot_id,
            ShootAccess.invite_email == data.email,
            ShootAccess.revoked_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already invited")

    # Also check by user_id if user already exists
    existing_user = await db.execute(select(User).where(User.email == data.email))
    user = existing_user.scalar_one_or_none()
    if user:
        existing_access = await db.execute(
            select(ShootAccess).where(
                ShootAccess.shoot_id == shoot_id,
                ShootAccess.user_id == user.id,
                ShootAccess.revoked_at.is_(None),
            )
        )
        if existing_access.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already has access")

    # Generate invite
    token = secrets.token_urlsafe(32)
    code = secrets.token_urlsafe(6).upper()[:8]

    access = ShootAccess(
        shoot_id=shoot_id,
        user_class=data.user_class,
        access_code=code,
        qr_data=f"wfc://{shoot_id}/{code}",
        invite_token=token,
        invite_email=data.email,
    )
    db.add(access)
    await db.commit()

    # Send email (async, fire-and-forget)
    invite_url = f"https://app.wificinemas.com/invite/{token}"
    await send_invite_email(
        to_email=data.email,
        to_name=data.name or data.email,
        shoot_name=shoot.name,
        inviter_name=current_user.name,
        invite_url=invite_url,
    )

    return InviteResponse(
        invite_token=token,
        invite_url=invite_url,
        email=data.email,
        shoot_id=shoot_id,
        user_class=data.user_class,
    )


@router.get("/accept/{token}", response_model=AcceptResponse)
async def accept_invite(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """User clicks invite link → account created, access granted."""
    result = await db.execute(
        select(ShootAccess).where(
            ShootAccess.invite_token == token,
            ShootAccess.revoked_at.is_(None),
        )
    )
    access = result.scalar_one_or_none()
    if not access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or expired invitation")

    if access.invite_accepted_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation already accepted")

    # Find or create user
    email = access.invite_email
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()

    if not user:
        user = User(email=email, name=email.split("@")[0], role="user")
        db.add(user)
        await db.flush()

    # Link access to user
    access.user_id = user.id
    access.invite_accepted_at = datetime.now(timezone.utc)
    await db.commit()

    # Get shoot name
    shoot_result = await db.execute(select(Shoot).where(Shoot.id == access.shoot_id))
    shoot = shoot_result.scalar_one_or_none()

    return AcceptResponse(
        message="Bienvenue! Accès accordé.",
        user_id=user.id,
        shoot_id=access.shoot_id,
        shoot_name=shoot.name if shoot else "Unknown",
    )


@router.get("/shoot/{shoot_id}/pending")
async def list_pending_invites(
    shoot_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin sees pending invitations for their shoot."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your shoot")

    result = await db.execute(
        select(ShootAccess).where(
            ShootAccess.shoot_id == shoot_id,
            ShootAccess.invite_email.is_not(None),
            ShootAccess.invite_accepted_at.is_(None),
            ShootAccess.revoked_at.is_(None),
        )
    )
    pending = result.scalars().all()
    return {
        "shoot_id": str(shoot_id),
        "pending": [
            {
                "email": a.invite_email,
                "user_class": a.user_class,
                "invited_at": a.granted_at.isoformat() if a.granted_at else None,
            }
            for a in pending
        ],
        "total": len(pending),
    }


@router.delete("/shoot/{shoot_id}/revoke/{email}")
async def revoke_invite(
    shoot_id: uuid.UUID,
    email: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin revokes a pending invitation."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your shoot")

    result = await db.execute(
        select(ShootAccess).where(
            ShootAccess.shoot_id == shoot_id,
            ShootAccess.invite_email == email,
            ShootAccess.revoked_at.is_(None),
        )
    )
    access = result.scalar_one_or_none()
    if not access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending invite for this email")

    access.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "revoked", "email": email}
