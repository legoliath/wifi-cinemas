import uuid
from datetime import datetime
from pydantic import BaseModel


class RoofTelemetryIn(BaseModel):
    """Payload from the roof phone (sent every ~2s via WebSocket or POST)."""
    signal_strength: float = 0.0
    obstruction_pct: float = 0.0
    tilt_x: float = 0.0
    tilt_y: float = 0.0
    compass_heading: float = 0.0
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None
    download_mbps: float = 0.0
    upload_mbps: float = 0.0
    latency_ms: float = 0.0
    phone_battery_pct: float = 100.0
    is_charging: bool = False
    source_device: str | None = None


class RoofTelemetryOut(RoofTelemetryIn):
    id: uuid.UUID
    shoot_id: uuid.UUID
    timestamp: datetime
    model_config = {"from_attributes": True}


class RoofAdjustmentHint(BaseModel):
    """Computed hint for the tech: which direction to adjust the dish."""
    action: str  # "hold" | "adjust"
    direction: str | None = None  # "left" | "right" | "forward" | "backward"
    magnitude: str | None = None  # "slight" | "moderate" | "large"
    obstruction_pct: float
    signal_strength: float
    message: str  # Human-readable: "Move dish slightly to the left"
