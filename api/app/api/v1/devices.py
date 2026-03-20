"""Device management + QoS priority system.

Devices = anything on the WiFi: phones, laptops, cameras, Teradek, NAS, etc.
Super admin / owner sets priority per device. Backend enforces via UniFi API.
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.api.deps import get_current_user, check_shoot_admin, check_shoot_access
from app.models.user import User
from app.models.device import Device
from app.services.unifi import unifi_client

router = APIRouter(prefix="/devices", tags=["Devices & QoS"])


# ── Schemas ────────────────────────────────────────────────────────────

class DeviceResponse(BaseModel):
    id: uuid.UUID
    mac: str
    hostname: str | None
    label: str | None
    category: str
    priority: str
    is_blocked: bool
    bandwidth_limit_down: int | None
    bandwidth_limit_up: int | None
    user_id: uuid.UUID | None
    shoot_id: uuid.UUID | None
    rx_bytes: float
    tx_bytes: float
    signal_dbm: int | None
    connected_at: datetime
    last_seen: datetime
    model_config = {"from_attributes": True}


class DeviceUpdate(BaseModel):
    label: str | None = None
    category: str | None = None  # phone | computer | cinema_equipment | other
    priority: str | None = None  # critical | normal | low | blocked
    bandwidth_limit_down: int | None = None  # kbps
    bandwidth_limit_up: int | None = None
    user_id: uuid.UUID | None = None


class DeviceListResponse(BaseModel):
    devices: list[DeviceResponse]
    total: int
    by_priority: dict[str, int]  # {"critical": 3, "normal": 15, "low": 5, "blocked": 1}
    by_category: dict[str, int]


class QoSPreset(BaseModel):
    """Bulk QoS preset for quick setup."""
    shoot_id: uuid.UUID
    rules: list[dict]  # [{"category": "cinema_equipment", "priority": "critical"}, ...]


# ── Endpoints ──────────────────────────────────────────────────────────

@router.get("/shoot/{shoot_id}", response_model=DeviceListResponse)
async def list_devices(
    shoot_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    category: str | None = None,
    priority: str | None = None,
):
    """List all devices on a shoot. Tech+ can view. Super admin+ can manage."""
    if not await check_shoot_access(current_user, shoot_id, db, min_role="tech"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tech access required")

    query = select(Device).where(Device.shoot_id == shoot_id, Device.disconnected_at.is_(None))
    if category:
        query = query.where(Device.category == category)
    if priority:
        query = query.where(Device.priority == priority)

    result = await db.execute(query.order_by(Device.priority, Device.last_seen.desc()))
    devices = result.scalars().all()

    # Counts
    all_result = await db.execute(
        select(Device).where(Device.shoot_id == shoot_id, Device.disconnected_at.is_(None))
    )
    all_devices = all_result.scalars().all()

    by_priority = {}
    by_category = {}
    for d in all_devices:
        by_priority[d.priority] = by_priority.get(d.priority, 0) + 1
        by_category[d.category] = by_category.get(d.category, 0) + 1

    return DeviceListResponse(devices=devices, total=len(devices),
                              by_priority=by_priority, by_category=by_category)


@router.get("/shoot/{shoot_id}/sync")
async def sync_devices(
    shoot_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Pull connected clients from UniFi and sync with DB.
    New devices get category=other, priority=normal.
    Existing devices get updated stats."""
    if not await check_shoot_access(current_user, shoot_id, db, min_role="tech"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tech access required")

    live_clients = await unifi_client.get_clients()
    synced = 0
    new = 0

    for client in live_clients:
        mac = client["mac"]
        result = await db.execute(
            select(Device).where(Device.mac == mac, Device.shoot_id == shoot_id)
        )
        device = result.scalar_one_or_none()

        if device:
            # Update stats
            device.hostname = client.get("hostname") or device.hostname
            device.ap_name = client.get("ap_name")
            device.rx_bytes = client.get("rx_bytes", 0)
            device.tx_bytes = client.get("tx_bytes", 0)
            device.signal_dbm = client.get("signal", None)
            device.last_seen = datetime.now(timezone.utc)
            device.disconnected_at = None
            synced += 1
        else:
            # New device
            device = Device(
                mac=mac,
                hostname=client.get("hostname"),
                shoot_id=shoot_id,
                ap_name=client.get("ap_name"),
                category=_guess_category(client.get("hostname", "")),
                priority="normal",
                rx_bytes=client.get("rx_bytes", 0),
                tx_bytes=client.get("tx_bytes", 0),
                signal_dbm=client.get("signal", None),
            )
            db.add(device)
            new += 1

    await db.commit()
    return {"synced": synced, "new": new, "total": synced + new}


@router.patch("/shoot/{shoot_id}/{device_id}", response_model=DeviceResponse)
async def update_device(
    shoot_id: uuid.UUID,
    device_id: uuid.UUID,
    data: DeviceUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update device label, category, priority, bandwidth limits.
    Super admin or shoot admin only."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shoot admin access required")

    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.shoot_id == shoot_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)

    # If priority changed to blocked, enforce via UniFi
    if data.priority == "blocked":
        device.is_blocked = True
        await unifi_client.block_client(device.mac)
    elif data.priority and data.priority != "blocked" and device.is_blocked:
        device.is_blocked = False
        # TODO: unifi_client.unblock_client(device.mac)

    await db.commit()
    await db.refresh(device)
    return device


@router.post("/shoot/{shoot_id}/block/{device_id}", status_code=status.HTTP_200_OK)
async def block_device(
    shoot_id: uuid.UUID,
    device_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """One-tap block. Super admin / shoot admin."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shoot admin access required")

    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.shoot_id == shoot_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    device.is_blocked = True
    device.priority = "blocked"
    await unifi_client.block_client(device.mac)
    await db.commit()
    return {"status": "blocked", "mac": device.mac, "label": device.label or device.hostname}


@router.post("/shoot/{shoot_id}/qos-preset")
async def apply_qos_preset(
    shoot_id: uuid.UUID,
    preset: QoSPreset,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Bulk QoS: apply priority rules by category.
    Example: all cinema_equipment → critical, all phone → normal."""
    if not await check_shoot_admin(current_user, shoot_id, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Shoot admin access required")

    updated = 0
    for rule in preset.rules:
        cat = rule.get("category")
        prio = rule.get("priority", "normal")
        bw_down = rule.get("bandwidth_limit_down")
        bw_up = rule.get("bandwidth_limit_up")

        if not cat:
            continue

        result = await db.execute(
            select(Device).where(
                Device.shoot_id == shoot_id,
                Device.category == cat,
                Device.disconnected_at.is_(None),
            )
        )
        devices = result.scalars().all()
        for device in devices:
            device.priority = prio
            device.is_blocked = prio == "blocked"
            if bw_down is not None:
                device.bandwidth_limit_down = bw_down
            if bw_up is not None:
                device.bandwidth_limit_up = bw_up
            updated += 1

    await db.commit()
    return {"updated": updated, "rules_applied": len(preset.rules)}


def _guess_category(hostname: str) -> str:
    """Best-effort category guess from hostname."""
    h = hostname.lower()
    if any(k in h for k in ("iphone", "ipad", "pixel", "galaxy", "android")):
        return "phone"
    if any(k in h for k in ("macbook", "laptop", "desktop", "pc", "imac")):
        return "computer"
    if any(k in h for k in ("teradek", "camera", "arri", "red", "bmd", "blackmagic", "atomos", "shogun")):
        return "cinema_equipment"
    return "other"
