import uuid
from datetime import datetime
from pydantic import BaseModel

class NetworkStatus(BaseModel):
    shoot_id: uuid.UUID
    is_online: bool
    source: str
    is_failover: bool
    download_mbps: float
    upload_mbps: float
    latency_ms: float
    packet_loss: float
    connected_devices: int
    last_updated: datetime

class MetricPoint(BaseModel):
    timestamp: datetime
    download_mbps: float
    upload_mbps: float
    latency_ms: float
    packet_loss: float
    source: str
    is_failover: bool

class MetricsHistoryResponse(BaseModel):
    shoot_id: uuid.UUID
    metrics: list[MetricPoint]
    period: str

class DeviceInfo(BaseModel):
    id: uuid.UUID
    mac: str
    hostname: str | None
    user_name: str | None
    ap_name: str | None
    connected_at: datetime

class DeviceListResponse(BaseModel):
    devices: list[DeviceInfo]
    total: int
