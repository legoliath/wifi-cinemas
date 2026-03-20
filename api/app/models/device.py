import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mac: Mapped[str] = mapped_column(String(17), index=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Optional link to a user (phones/laptops). NULL for equipment (cameras, Teradek, NAS)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    shoot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("shoots.id"), nullable=True)
    ap_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Device classification
    category: Mapped[str] = mapped_column(String(30), default="other")
    # "phone" | "computer" | "cinema_equipment" | "other"

    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Human label: "Teradek Bolt 4K #2", "DIT MacBook Pro", "Caméra A"

    # QoS / Priority (set by super_admin)
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    # "critical" | "normal" | "low" | "blocked"

    bandwidth_limit_down: Mapped[int | None] = mapped_column(Integer, nullable=True)  # kbps, NULL = unlimited
    bandwidth_limit_up: Mapped[int | None] = mapped_column(Integer, nullable=True)    # kbps, NULL = unlimited

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Stats (updated from UniFi polling)
    rx_bytes: Mapped[float] = mapped_column(Float, default=0.0)
    tx_bytes: Mapped[float] = mapped_column(Float, default=0.0)
    signal_dbm: Mapped[int | None] = mapped_column(Integer, nullable=True)

    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="devices")
    shoot = relationship("Shoot", back_populates="devices")
