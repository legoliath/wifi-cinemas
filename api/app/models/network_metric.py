import uuid
from datetime import datetime
from sqlalchemy import Float, DateTime, ForeignKey, Boolean, Enum as SAEnum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class NetworkMetric(Base):
    __tablename__ = "network_metrics"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shoot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("shoots.id"), index=True)
    kit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("kits.id"), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    download_mbps: Mapped[float] = mapped_column(Float, default=0.0)
    upload_mbps: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    packet_loss: Mapped[float] = mapped_column(Float, default=0.0)
    source: Mapped[str] = mapped_column(SAEnum("starlink","5g","both", name="network_source"), default="starlink")
    is_failover: Mapped[bool] = mapped_column(Boolean, default=False)
    shoot = relationship("Shoot", back_populates="metrics")
