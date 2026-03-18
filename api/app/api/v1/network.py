import uuid, random
from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.device import Device
from app.schemas.network import NetworkStatus, DeviceListResponse, DeviceInfo

router = APIRouter(prefix="/network", tags=["Network"])

@router.get("/status/{shoot_id}", response_model=NetworkStatus)
async def get_network_status(shoot_id: uuid.UUID, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Device).where(Device.shoot_id == shoot_id, Device.disconnected_at.is_(None)))
    devices = len(result.scalars().all())
    return NetworkStatus(shoot_id=shoot_id, is_online=True, source="starlink", is_failover=False, download_mbps=round(random.uniform(80,200),1), upload_mbps=round(random.uniform(15,40),1), latency_ms=round(random.uniform(20,45),1), packet_loss=round(random.uniform(0,0.5),2), connected_devices=devices, last_updated=datetime.now(timezone.utc))

@router.get("/devices/{shoot_id}", response_model=DeviceListResponse)
async def get_devices(shoot_id: uuid.UUID, current_user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Device).where(Device.shoot_id == shoot_id, Device.disconnected_at.is_(None)))
    devices = result.scalars().all()
    return DeviceListResponse(devices=[DeviceInfo(id=d.id, mac=d.mac, hostname=d.hostname, user_name=None, ap_name=d.ap_name, connected_at=d.connected_at) for d in devices], total=len(devices))
