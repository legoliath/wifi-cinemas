import uuid
from datetime import datetime
from sqlalchemy import Float, String, DateTime, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class RoofTelemetry(Base):
    """Snapshot from the roof-mounted phone — persisted for history/debug."""
    __tablename__ = "roof_telemetry"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shoot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shoots.id"), index=True)
    # Signal
    signal_strength: Mapped[float] = mapped_column(Float, default=0.0)  # dB or 0-100%
    obstruction_pct: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0 - 1.0
    # Orientation (accelerometer / gyro)
    tilt_x: Mapped[float] = mapped_column(Float, default=0.0)  # degrees
    tilt_y: Mapped[float] = mapped_column(Float, default=0.0)  # degrees
    compass_heading: Mapped[float] = mapped_column(Float, default=0.0)  # 0-360
    # GPS
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    altitude_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Network (from phone perspective)
    download_mbps: Mapped[float] = mapped_column(Float, default=0.0)
    upload_mbps: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    # Meta
    phone_battery_pct: Mapped[float] = mapped_column(Float, default=100.0)
    is_charging: Mapped[bool] = mapped_column(Boolean, default=False)
    source_device: Mapped[str | None] = mapped_column(String(100), nullable=True)  # "iPhone 15 Pro"
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
