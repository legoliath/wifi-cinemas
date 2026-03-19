"""Network endpoints — live data from Starlink + Peplink + UniFi."""
import uuid
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, require_tech_or_admin
from app.models.user import User
from app.models.device import Device
from app.services.starlink import starlink_client
from app.services.peplink import peplink_client
from app.services.unifi import unifi_client
from app.schemas.network import NetworkStatus, DeviceListResponse, DeviceInfo

router = APIRouter(prefix="/network", tags=["Network"])


@router.get("/status/{shoot_id}", response_model=NetworkStatus)
async def get_network_status(
    shoot_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Aggregate network status from Starlink, Peplink, and UniFi."""
    # Starlink
    starlink = await starlink_client.get_status()

    # Peplink WAN
    wan = await peplink_client.get_wan_status()

    # UniFi clients count
    clients = await unifi_client.get_clients()

    return NetworkStatus(
        shoot_id=shoot_id,
        is_online=starlink.get("state") == "CONNECTED",
        source="5g" if wan.get("failover_active") else "starlink",
        is_failover=wan.get("failover_active", False),
        download_mbps=starlink.get("download_mbps", 0),
        upload_mbps=starlink.get("upload_mbps", 0),
        latency_ms=starlink.get("latency_ms", 0),
        packet_loss=starlink.get("obstruction_pct", 0),
        connected_devices=len(clients),
        last_updated=datetime.now(timezone.utc),
    )


@router.get("/starlink")
async def get_starlink_status(
    current_user: Annotated[User, Depends(require_tech_or_admin)],
):
    """Raw Starlink dish status (tech/admin only)."""
    status = await starlink_client.get_status()
    obstruction = await starlink_client.get_obstruction_data()
    return {"dish": status, "obstruction": obstruction}


@router.get("/wan")
async def get_wan_status(
    current_user: Annotated[User, Depends(require_tech_or_admin)],
):
    """Peplink WAN status + cellular data usage (tech/admin only)."""
    wan = await peplink_client.get_wan_status()
    usage = await peplink_client.get_data_usage()
    device = await peplink_client.get_device_info()
    return {"wan": wan, "data_usage": usage, "device": device}


@router.get("/access-points")
async def get_access_points(
    current_user: Annotated[User, Depends(require_tech_or_admin)],
):
    """UniFi access points status (tech/admin only)."""
    return await unifi_client.get_access_points()


@router.get("/devices/{shoot_id}", response_model=DeviceListResponse)
async def get_devices(
    shoot_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Connected devices from UniFi (live) + DB history."""
    # Live from UniFi
    live_clients = await unifi_client.get_clients()

    devices = [
        DeviceInfo(
            id=uuid.uuid4(),  # Generated since these are live
            mac=c["mac"],
            hostname=c.get("hostname"),
            user_name=None,
            ap_name=c.get("ap_name"),
            connected_at=datetime.now(timezone.utc),
        )
        for c in live_clients
    ]

    return DeviceListResponse(devices=devices, total=len(devices))
