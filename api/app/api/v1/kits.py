"""Kit management — owner only. Hardware inventory (Starlink + Peplink + UniFi)."""
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import require_owner
from app.models.user import User
from app.models.kit import Kit
from pydantic import BaseModel


class KitCreate(BaseModel):
    name: str
    starlink_serial: str | None = None
    peplink_serial: str | None = None
    unifi_site_id: str | None = None
    admin_ssid: str


class KitUpdate(BaseModel):
    name: str | None = None
    starlink_serial: str | None = None
    peplink_serial: str | None = None
    unifi_site_id: str | None = None
    admin_ssid: str | None = None
    status: str | None = None


class KitResponse(BaseModel):
    id: uuid.UUID
    name: str
    starlink_serial: str | None
    peplink_serial: str | None
    unifi_site_id: str | None
    admin_ssid: str
    status: str
    model_config = {"from_attributes": True}


router = APIRouter(prefix="/kits", tags=["Kits"])


@router.get("", response_model=list[KitResponse])
async def list_kits(
    owner: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all hardware kits."""
    result = await db.execute(select(Kit))
    return result.scalars().all()


@router.post("", response_model=KitResponse, status_code=status.HTTP_201_CREATED)
async def create_kit(
    data: KitCreate,
    owner: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new hardware kit."""
    kit = Kit(
        name=data.name,
        starlink_serial=data.starlink_serial,
        peplink_serial=data.peplink_serial,
        unifi_site_id=data.unifi_site_id,
        admin_ssid=data.admin_ssid,
    )
    db.add(kit)
    await db.commit()
    await db.refresh(kit)
    return kit


@router.get("/{kit_id}", response_model=KitResponse)
async def get_kit(
    kit_id: uuid.UUID,
    owner: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Kit).where(Kit.id == kit_id))
    kit = result.scalar_one_or_none()
    if not kit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kit not found")
    return kit


@router.patch("/{kit_id}", response_model=KitResponse)
async def update_kit(
    kit_id: uuid.UUID,
    data: KitUpdate,
    owner: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Kit).where(Kit.id == kit_id))
    kit = result.scalar_one_or_none()
    if not kit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kit not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(kit, field, value)
    await db.commit()
    await db.refresh(kit)
    return kit


@router.delete("/{kit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kit(
    kit_id: uuid.UUID,
    owner: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Kit).where(Kit.id == kit_id))
    kit = result.scalar_one_or_none()
    if not kit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kit not found")
    await db.delete(kit)
    await db.commit()
